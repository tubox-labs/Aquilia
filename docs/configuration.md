# Configuration Reference

Aquilia configuration is Python-native. The implementation centers on `Workspace`, `Module`, `Integration`, `AquilaConfig`, dotenv loading, and `ConfigLoader`.

## Source Files

- `aquilia/config_builders.py`: fluent `Workspace`, `Module`, and `Integration` builders.
- `aquilia/pyconfig.py`: class-based `AquilaConfig`, `Env`, `Secret`, dotenv policies, and `PyConfigLoader`.
- `aquilia/config.py`: `ConfigLoader`, namespace access, environment variable merging, and subsystem config accessors.
- `aquilia/integrations/*.py`: typed integration config objects.

## ConfigLoader Precedence

`ConfigLoader.load()` merges in this order:

1. Workspace structure from `workspace.py` or `aquilia.py`.
2. Legacy `config/env.py` if it exists.
3. Explicit `.env` file if `env_file` is passed.
4. Native dotenv auto-load through `DotEnvLoader.ensure_loaded()`.
5. `AQ_` environment variables, with double underscores converted to nested keys.
6. Manual overrides.

## Environment Variables

- `AQUILIA_ENV`: runtime mode used by `AquiliaRuntime` and entrypoint (`dev`, `test`, `prod`, or `production` normalized to `prod`).
- `AQUILIA_WORKSPACE`: workspace root for runtime/entrypoint resolution.
- `AQ_*`: generic config overlay consumed by `ConfigLoader`; `AQ_AUTH__TOKENS__SECRET_KEY` becomes `auth.tokens.secret_key`.
- `AQ_ENV`: legacy/pyconfig environment selector used by `AquilaConfig.for_env()` fallback paths.
- `AQ_SECRET_KEY` and `SECRET_KEY`: signing secret fallbacks used by `AquiliaServer._bootstrap_signing()`.

## YAML Status

YAML config is removed. `ConfigLoader._load_yaml_file()` raises `ConfigInvalidFault` and instructs users to migrate to `AquilaConfig` classes in `workspace.py`.

## Workspace Builder Surface

See [Core Configuration](modules/core/configuration.md) and [Integrations Configuration](modules/integrations/configuration.md) for source-extracted builder methods and integration classes.
