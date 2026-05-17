# Multi-Module Aquilia Native Starter

## Purpose

Production-shaped commerce workspace demonstrating how Aquilia modules compose in one runtime.

## Architecture

- `workspace.py` registers `accounts`, `catalog`, `orders`, `notifications`, `realtime`, and `operations`.
- Module imports/exports model dependency boundaries: `orders` imports `accounts` and `catalog`; `realtime` imports `accounts` and `orders`.
- Integrations cover database, tasks, storage, mail, templates, OpenAPI, versioning, admin, DI, routing, faults, cache, i18n, sessions, security, and telemetry.
- HTTP modules keep controllers thin and services stateful.
- `realtime` demonstrates socket fanout; `notifications` demonstrates task-backed mail behavior.

## Run

```bash
cd examples/multi_module_native_app
python -m uvicorn runtime:app --reload --port 8050
```

Expected behavior: operational endpoints under `/ops`, catalog/order/account endpoints under their module prefixes, and order socket routes under `/ws/orders/:tenant`.

## Test

```bash
python -m pytest examples/multi_module_native_app -q
```

## Common Pitfalls

- This is local-first: memory stores, console mail, local storage paths, and sqlite config are intentionally replaceable.
- Auth-protected order routes require runtime auth state.
- Cross-module imports are declared in workspace and manifests; do not instantiate another module's private service by path unless it is exported.

## Extension Ideas

Replace in-memory services with model-backed repositories, add a Redis cache/socket adapter, configure SMTP/SES/SendGrid, add admin model registrations, and add OpenAPI snapshot tests.

## Related APIs

`Workspace`, `Module.imports`, `AppManifest.exports`, `Integration.cache`, `Integration.di`, typed integrations, `SessionPolicy`, `TaskManager`, sockets, templates, i18n, versioning, admin.
