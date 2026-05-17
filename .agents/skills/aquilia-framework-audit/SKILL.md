---
name: aquilia-framework-audit
description: "Audit and navigate the Aquilia framework from actual source code. Use when a user asks to understand Aquilia architecture, execution flow, subsystem boundaries, code ownership, or to derive changes/skills/docs from implementation rather than assumptions."
---

# Aquilia Framework Audit

## Purpose
Build an implementation-backed model of Aquilia before editing framework code, docs, examples, or skills.

## Trigger Conditions
Use for Aquilia architecture audits, subsystem maps, runtime tracing, source-backed documentation, and any cross-cutting change that touches runtime, manifests, DI, CLI, integrations, or generated project structure.

## Inputs
- Repository root containing `aquilia/`, `tests/`, `examples/`, `docs/modules/`, and `pyproject.toml`.
- Optional subsystem or workflow name.
- Optional output format: report, checklist, risk map, or implementation plan.

## Execution Flow
1. Start read-only. Inspect `pyproject.toml`, `README.md`, `GUIDE.md`, `aquilia/__init__.py`, `aquilia/runtime.py`, `aquilia/server.py`, `aquilia/asgi.py`, `aquilia/manifest.py`, `aquilia/config_builders.py`, and `aquilia/cli/__main__.py`.
2. Trace bootstrap: `workspace.py` -> `ConfigLoader` -> `AquiliaRuntime.configure/discover/bootstrap` -> `AquiliaServer` -> `Aquilary.from_manifests` -> `RuntimeRegistry` -> `ControllerRouter`/`ASGIAdapter`.
3. Inventory affected packages with `rg` before editing. Use examples and tests only to confirm source behavior.
4. Report findings with file anchors and separate implemented behavior from inferred intent.

## Constraints
- Do not infer capabilities from package names, README claims, or docs alone.
- Treat `workspace.py` as orchestration and module `manifest.py` as module internals.
- Note deprecated surfaces such as `Module.register_controllers()` and `AppManifest.database` instead of recommending them.

## Implementation Anchors
`aquilia/runtime.py`, `aquilia/server.py`, `aquilia/asgi.py`, `aquilia/aquilary/core.py`, `aquilia/manifest.py`, `aquilia/config_builders.py`, `aquilia/cli/__main__.py`, `examples/reference_suite/`.

## Examples
- "Audit why a controller route is not registered in my Aquilia app."
- "Map every subsystem touched by adding a new workspace integration."
- "Create a source-backed architecture summary for Aquilia runtime startup."

## Failure Handling
If source and docs disagree, trust source and flag docs as stale. If imports execute workspace code unexpectedly, switch to static inspection with `rg`, `sed`, and AST parsing. If generated and backup files coexist, identify the canonical runtime path before changing anything.
