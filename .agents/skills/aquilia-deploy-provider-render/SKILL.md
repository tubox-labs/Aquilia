---
name: aquilia-deploy-provider-render
description: "Generate and operate Aquilia deployment/provider workflows. Use for aq deploy dockerfile/compose/kubernetes/nginx/ci/monitoring/env/all/makefile/render, deployment generators, Render provider login/status/env vars/deploy/destroy/status, and provider credential store."
---

# Aquilia Deploy Provider Render

## Purpose
Use Aquilia's deployment generators and Render provider integration without inventing deployment behavior.

## Trigger Conditions
Use for Dockerfile, docker-compose, Kubernetes, Nginx, CI, monitoring, env files, Makefile generation, Render deployments, provider auth, or Render environment variable management.

## Inputs
- Workspace root, output directory, force/dry-run flags, monitoring/CI provider choice, image/region/plan/service name, Render token, env var names/values.

## Execution Flow
1. For generated deployment assets, use `aq deploy` subcommands and generator code in `deploy_gen.py`.
2. Prefer `--dry-run` before writing deployment files when available.
3. For Render auth, use `aq provider login render` and credential store paths.
4. For Render deploys, use `aq deploy render` flags for service, plan, region, instances, status, or destroy.
5. Manage Render env vars with `aq provider render env list/set/delete`.

## Constraints
- Do not expose Render tokens; credential store encrypts and audits provider credentials.
- Do not run destructive provider actions such as destroy without explicit user approval.
- Generated deployment files should reflect workspace introspection rather than static assumptions.

## Implementation Anchors
`aquilia/cli/commands/deploy_gen.py`, `aquilia/cli/generators/deployment.py`, `aquilia/cli/commands/provider.py`, `aquilia/providers/render/`, `examples/provider_render_deploy_app/`, `tests/test_render_provider.py`.

## Examples
- `aq deploy dockerfile --dev --output . --dry-run`.
- `aq deploy all --ci-provider github --monitoring`.
- `aq provider render env set DJANGO_SECRET --service my-service`.

## Failure Handling
If Docker/Kubernetes/Render tools are missing, surface the missing command. If provider credentials are absent, direct the user to provider login. For dry-run, never write files or call remote mutating APIs.
