# Aquilia Examples

These examples are starter blueprints for real Aquilia applications. Each directory follows the same structure that the framework generators and runtime expect:

- `workspace.py` describes the application, module pointers, route prefixes, and integrations.
- `runtime.py` exposes an ASGI `app` from `AquiliaRuntime`.
- `modules/<name>/manifest.py` declares controllers, services, socket controllers, tasks, models, and fault settings for that module.
- Controllers stay thin and call services.
- Blueprints validate inbound and outbound contracts.
- Services hold business behavior and hide storage choices.

The examples favor in-memory services where that keeps the starter runnable without external services. The module boundaries are still production-shaped, so a database, Redis, durable queue, or cloud storage backend can be introduced without rewriting controllers.

## Starters

| Directory | Focus |
| --- | --- |
| `rest_api_blueprint` | Versioned product REST API with blueprints, filtering, validation, and health checks. |
| `crud_app` | Project tracker CRUD app with models, blueprints, repository service, partial updates, soft deletion, and tests. |
| `auth_app` | Authentication app with registration, login, token issuance, protected profile route, and admin guard example. |
| `websocket_app` | Chat style WebSocket app with rooms, event handlers, acknowledgements, presence, and a small HTTP inspection API. |
| `background_jobs` | Background job app with task descriptors, queues, scheduled cleanup, job status, and controller-triggered dispatch. |
| `multi_module_native_app` | Complete multi-module Aquilia-native starter combining HTTP, auth, sessions, cache, storage, mail, i18n, tasks, sockets, versioning, templates, admin, and operational endpoints. |
