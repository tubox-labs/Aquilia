---
name: aquilia-config-integration-manager
description: "Manage Aquilia Python-native configuration and typed integrations. Use for Integration.* builders, aquilia.integrations dataclasses, database/cache/storage/tasks/mail/templates/admin/openapi/security/session config, Env, Secret, and ConfigLoader behavior."
---

# Aquilia Config Integration Manager

## Purpose
Configure Aquilia apps with the implemented builder and integration objects instead of ad hoc dictionaries.

## Trigger Conditions
Use when changing `workspace.py` integrations, env config, typed database config, security/telemetry settings, or integration dataclasses under `aquilia/integrations/`.

## Inputs
- Target integration type and values.
- Environment names and required secrets.
- Whether config should be global workspace config or module-level manifest config.

## Execution Flow
1. Prefer typed integration classes from `aquilia.integrations` or `Integration.*` builder methods from `config_builders.py`.
2. Use `Workspace.integrate(...)` for integration objects and `Workspace.database/tasks/storage/security/telemetry/sessions/i18n` for common convenience flows.
3. Use `AquilaConfig`, `Env`, and `Secret` for environment variants and secret resolution.
4. Confirm `to_dict()` output matches what `ConfigLoader` and `AquiliaServer` consume.
5. Keep module-specific component settings in `AppManifest` and global operational settings in `Workspace`.

## Constraints
- Do not leak `Secret.reveal()` output into logs or generated docs.
- Do not configure database through `AppManifest.database` for new code.
- Validate whether an integration returns a dict or an `IntegrationConfig` object; `Workspace.integrate()` handles both.

## Implementation Anchors
`aquilia/config_builders.py`, `aquilia/pyconfig.py`, `aquilia/config.py`, `aquilia/integrations/*.py`, `tests/test_integration_configs.py`, `tests/test_integration_wiring.py`.

## Examples
- Add `Integration.database(config=PostgresConfig(...))`.
- Add `MailIntegration(default_from=..., providers=[ConsoleProvider(...)])`.
- Define `ProdEnv(BaseEnv)` with `Secret(env="AQ_SECRET_KEY", required=True)`.

## Failure Handling
If config is missing, check `ConfigLoader.load()` merge order and env prefix. If a secret is required and absent, expect `ConfigMissingFault`. If a subsystem ignores config, trace its `get_*_config()` method or server setup path.
