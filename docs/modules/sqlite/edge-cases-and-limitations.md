# Sqlite Edge Cases And Limitations

Native async SQLite compatibility layer, connection pool, transactions, cursors, rows, PRAGMAs, backup, metrics, and errors.

## Source-Backed Limits

- No module-specific edge branch was detected beyond optional imports, validation, and dependency availability.

## Fault And Error Classes Detected

`SqliteError`, `SqliteConnectionError`, `PoolExhaustedError`, `SqliteQueryError`, `SqliteIntegrityError`, `SqliteSchemaError`, `SqliteTimeoutError`, `SqliteSecurityError`

## Operational Boundaries

- Optional external libraries are only required when the corresponding provider/backend/runtime is configured.
- Deprecated APIs generally warn when retained for migration rather than disappearing silently.
- Server startup intentionally degrades non-critical optional subsystems where source catches and logs exceptions.
- Use `api-reference.md` to check exact constructor defaults and method signatures before depending on behavior.

## Verification

- `aq doctor` for workspace/integration issues.
- `aq validate` for manifest issues.
- `aq inspect config` for merged configuration.
- `GET /_health` for live subsystem status once the app is running.
