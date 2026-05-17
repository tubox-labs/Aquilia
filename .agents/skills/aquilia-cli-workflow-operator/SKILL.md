---
name: aquilia-cli-workflow-operator
description: "Operate and extend the Aquilia aq CLI. Use for aq init/add/generate/validate/compile/run/serve/freeze/manifest/inspect/discover/analytics/mail/cache/i18n/db/ws/admin/provider/deploy/test commands and Click flag behavior."
---

# Aquilia Cli Workflow Operator

## Purpose
Use and modify Aquilia CLI workflows according to the actual Click command tree.

## Trigger Conditions
Use when the user asks about `aq` commands, CLI flags, project scaffolding, validation, inspection, run/serve, database migrations, WebSocket operations, provider/render auth, deployment generation, admin operations, or tests.

## Inputs
- Command or workflow goal.
- Workspace path and whether command may write files.
- Desired flags such as `--yes`, `--minimal`, `--json`, `--dry-run`, `--check`, `--sync`, or provider-specific values.

## Execution Flow
1. Inspect `aquilia/cli/__main__.py` for command registration and global flags.
2. For implementation, follow delegated command modules in `aquilia/cli/commands/` and generators in `aquilia/cli/generators/`.
3. Use dry-run/check/json flags when present for inspection before writes.
4. Keep interactive behavior compatible with `sys.stdin.isatty()` and `--yes`/non-interactive paths.
5. Validate generated code with `aq validate`, `aq inspect`, or relevant test commands.

## Constraints
- Operational commands require `workspace.py` through `_require_workspace()` except bootstrap-safe commands.
- Name validation rejects uppercase starts and non lowercase/digit/hyphen/underscore characters.
- Do not add undocumented flags without wiring them through command implementation and help text.

## Implementation Anchors
`aquilia/cli/__main__.py`, `aquilia/cli/commands/*.py`, `aquilia/cli/generators/*.py`, `aquilia/cli/utils/prompts.py`, `tests/test_cli_model_shell_line_editing.py`.

## Examples
- `aq init workspace my-api --minimal -y`
- `aq add module orders --depends-on=accounts --route-prefix=/orders`
- `aq db makemigrations --app inventory --format json`

## Failure Handling
If a command fails outside a workspace, check `_require_workspace`. If generated files are stale, use manifest/discovery commands. If a command shells out, preserve dry-run behavior and surface missing external binaries clearly.
