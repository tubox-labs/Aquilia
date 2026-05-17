# Provider Render Deploy App

## Purpose

Demonstrates provider/deployment configuration using Render dataclasses and dry-run planning without contacting the Render API.

## Architecture

- `workspace.py` wires `RenderIntegration`.
- `RenderDeploymentPlanner` converts integration config into `RenderDeployConfig`.
- `dry_run()` returns the exact service payload shape consumed by the Render deployer and CLI provider workflows.

## Setup

```bash
python -m pip install -e ".[dev]"
python -m pytest examples/provider_render_deploy_app -q
```

## Run

```bash
cd examples/provider_render_deploy_app
python -m uvicorn runtime:app --reload --port 8072
```

## Expected Behavior

`POST /deployments/render/dry-run` returns a Render service payload with image, plan, region, instance count, health path, and env vars.

## Common Pitfalls

- This app intentionally does not persist credentials or call the Render API.
- Use `aq provider login render` and `aq deploy render` for real deployments after reviewing generated payloads.

## Extension Ideas

Add credential-store checks, provider status, env-var sync, Docker image promotion, and rollback plan generation.

## Related APIs

`RenderIntegration`, `RenderDeployConfig`, `RenderEnvVar`, `RenderPlan`, `RenderRegion`, `DeployResult`.
