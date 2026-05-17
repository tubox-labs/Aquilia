# Multi-Module Aquilia Native Starter

This is a larger starter for teams that want to begin with the same boundaries they will keep in production. It combines major Aquilia subsystems in one workspace:

- HTTP controllers and blueprints
- Auth and session policy
- Cache and storage integration
- Mail integration through a console provider
- Background tasks
- WebSocket realtime module
- Versioning, OpenAPI, templates, static files, i18n, admin, and telemetry configuration
- Operations endpoints for health and runtime inspection

The app models a small commerce workflow. Accounts authenticate users, catalog owns products, orders owns checkout, notifications owns task-driven communication, realtime owns socket fanout, and operations owns health and administrative readouts.

The code intentionally keeps infrastructure local and replaceable. Start with memory and console backends, then swap integration configs for production providers.
