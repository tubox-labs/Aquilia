---
name: aquilia-discovery-manifest-sync
description: "Use Aquilia discovery and manifest synchronization workflows. Use for auto-discovery, PackageScanner, DiscoveryInspector, analytics, aq discover --sync/--dry-run/--json, manifest update/check/freeze, workspace module config generation, and component sync issues."
---

# Aquilia Discovery Manifest Sync

## Purpose
Discover controllers/services/models/tasks/sockets and synchronize manifests/workspace metadata safely.

## Trigger Conditions
Use for missing auto-discovered components, `aq discover`, `aq analytics`, `aq manifest update`, workspace module config regeneration, discovery reports, or manifest drift checks.

## Inputs
- Workspace path, module name, sync/check/freeze/dry-run/json mode.
- Desired component patterns and whether auto-discovery is enabled.

## Execution Flow
1. Inspect `AppManifest.auto_discover` and `discover_patterns`.
2. Use `RuntimeRegistry.perform_autodiscovery()` behavior as the runtime reference.
3. For CLI discovery, use `DiscoveryInspector` and `aq discover --dry-run` before `--sync`.
4. For manifest updates, use `aq manifest update <module> --check` in CI and `--freeze` for strict mode where implemented.
5. Preserve the workspace/manifest split: workspace modules are pointers; module manifests own components.

## Constraints
- Do not sync by regex alone when AST-based discovery is available.
- Do not write discovery changes without dry-run/check when the user asked for audit only.
- Avoid adding private modules or names beginning with `_`/`.`.

## Implementation Anchors
`aquilia/discovery/engine.py`, `aquilia/utils/scanner.py`, `aquilia/aquilary/core.py`, `aquilia/cli/commands/discover.py`, `aquilia/cli/commands/analytics.py`, `aquilia/cli/commands/manifest.py`, `aquilia/cli/generators/workspace.py`.

## Examples
- `aq discover --path . --dry-run --json`.
- `aq discover --sync` to update detected components.
- `aq manifest update orders --check` in CI.

## Failure Handling
If discovery imports have side effects, use AST/static mode. If sync would produce invalid Python, generators should skip writes after syntax validation. If components are still missing, check package names and `__init__.py` availability.
