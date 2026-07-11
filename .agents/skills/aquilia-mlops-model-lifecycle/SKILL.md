---
name: aquilia-mlops-model-lifecycle
description: "Build Aquilia MLOps model packaging, registry, serving, rollout, observability, plugins, lineage, experiments, export, and admin workflows. Use for aquilia.mlops APIs and aq pack/model/mlops-deploy/observe/export/plugin/lineage/experiment commands."
---

# Aquilia Mlops Model Lifecycle

## Purpose
Use Aquilia's implemented MLOps stack for model packaging, registry, runtime serving, deployment rollout, observability, plugins, lineage, and experiments.

## Trigger Conditions
Use for modelpack archives, registry push/inspect/verify, serving models, ONNX/edge export, drift detection, metrics, rollout plans, plugin management, lineage queries, and A/B experiments.

## Inputs
- Model path, name, version, framework/runtime, env lock, signing key, registry URL, rollout versions, drift data, plugin package, or experiment arms.

## Execution Flow
1. Use CLI groups from `mlops_cmds.py`: `pack`, `model`, `mlops-deploy`, `observe`, `export`, `plugin`, `lineage`, and `experiment`.
2. Use `MLOpsManifest`, runtime/base classes, registry service/storage, orchestrator, scheduler, and observe modules where programmatic integration is needed.
3. Configure workspace with `Integration.mlops(...)` or `Workspace.mlops(...)` when app-level MLOps is required.
4. Use contract APIs for request/response schemas when exposing MLOps endpoints.
5. Verify archives and signatures before deployment or registry push.

## Constraints
- Optional dependencies are split by extras: core mlops, onnx, torch, s3, bento, explain.
- Do not fake support for a runtime if `select_runtime` or exporter code does not implement it.
- Signing and registry credentials must not be committed.

## Implementation Anchors
`aquilia/mlops/`, `aquilia/cli/commands/mlops_cmds.py`, `aquilia/integrations/mlops.py`, `aquilia/admin/templates/mlops.html`, `tests/test_mlops_*.py`, `examples/mlops_model_registry_app/`.

## Examples
- `aq pack save model.pkl --name recommender --version 1.0.0 --framework sklearn`.
- `aq model serve modelpack.aq --runtime python --port 9000`.
- `aq mlops-deploy rollout fraud --from-version 1.0 --to-version 1.1 --strategy canary`.

## Failure Handling
Pack integrity/signature failures should stop deployment. Missing optional ML dependencies should produce actionable install guidance. Drift/metrics failures should map to MLOps observe faults.
