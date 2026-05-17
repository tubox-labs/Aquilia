# Database Configuration

## Configuration Entry Points

The implementation exposes the following configuration-like classes, policies, integrations, or dataclasses.

| Type | Source | Fields | Purpose |
| --- | --- | --- | --- |
| `AdapterCapabilities` | `aquilia/db/backends/base.py` | supports_returning: bool, supports_json_type: bool, supports_arrays: bool, supports_hstore: bool, supports_citext: bool, supports_upsert: bool, supports_savepoints: bool, supports_window_functions: bool, supports_cte: bool, param_style: str, null_ordering: bool, name: str | Describes what a specific backend supports. |
| `ColumnInfo` | `aquilia/db/backends/base.py` | name: str, data_type: str, nullable: bool, default: str &#124; None, primary_key: bool, unique: bool, max_length: int &#124; None | Introspection result for a single column. |
| `TableInfo` | `aquilia/db/backends/base.py` | name: str, columns: list[ColumnInfo], indexes: list[dict[str, Any]], foreign_keys: list[dict[str, Any]] | Introspection result for a table. |
| `IntrospectionResult` | `aquilia/db/backends/base.py` | tables: list[TableInfo] | Full database introspection result. |
| `DatabaseConfig` | `aquilia/db/configs.py` | engine: str, pool_size: int, pool_min_size: int, pool_max_size: int, echo: bool, auto_connect: bool, auto_create: bool, auto_migrate: bool, migrations_dir: str, connect_retries: int, connect_retry_delay: float, conn_max_age: int, ... | Base database configuration. |
| `SqliteConfig` | `aquilia/db/configs.py` | engine: str, path: str, journal_mode: str, foreign_keys: bool, busy_timeout: int | SQLite database configuration. |
| `PostgresConfig` | `aquilia/db/configs.py` | engine: str, host: str, port: int, name: str, database: str, user: str, password: str, schema: str, sslmode: str | PostgreSQL database configuration. |
| `MysqlConfig` | `aquilia/db/configs.py` | engine: str, host: str, port: int, name: str, database: str, user: str, password: str, charset: str, collation: str | MySQL / MariaDB database configuration. |
| `OracleConfig` | `aquilia/db/configs.py` | engine: str, host: str, port: int, service_name: str, database: str, user: str, password: str, sid: str, thick_mode: bool, encoding: str | Oracle database configuration. |

## Common Entry Points

- `DatabaseIntegration`
- `SqliteConfig`
- `PostgresConfig`
- `MysqlConfig`
- `OracleConfig`

## Precedence Model

Aquilia generally resolves configuration in this order:

1. Explicit constructor arguments or typed integration dataclass values.
2. `Workspace` builder methods and `Workspace.integrate(...)` output.
3. `ConfigLoader` defaults and environment overlays.
4. Runtime defaults inside the subsystem service or provider constructor.

When this module is registered through an `AppManifest`, keep component declarations inside `modules/<name>/manifest.py` and keep cross-cutting integration settings in `workspace.py`.

## Datatype Guidance

- Prefer typed dataclasses, policy objects, and config objects listed above when they exist.
- Keep secret values in environment-backed config, not literal strings in committed workspace files.
- Keep runtime-only state in services, stores, providers, or request state rather than static configuration.
- Use `to_dict()` on integration dataclasses when you need to inspect exactly what enters `ConfigLoader`.
