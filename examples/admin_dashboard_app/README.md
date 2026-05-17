# Admin Dashboard App

## Purpose

Demonstrates Aquilia admin model registration, role-based admin permission checks, audit-style service events, and admin workspace integration.

## Architecture

- `workspace.py` enables `AdminIntegration` with audit, monitoring, and testing modules.
- `modules/adminops/models.py` declares a real Aquilia `Model`.
- `modules/adminops/admin.py` registers that model through `@register(SupportTicket)` and `ModelAdmin`.
- `modules/adminops/manifest.py` declares the controller, service, and model through `AppManifest`.

## Setup

```bash
python -m pip install -e ".[dev]"
python -m pytest examples/admin_dashboard_app -q
```

## Run

```bash
cd examples/admin_dashboard_app
python -m uvicorn runtime:app --reload --port 8061
```

## Expected Behavior

`GET /adminops/dashboard` returns ticket counts and permission-derived capability flags. The service tests verify that staff can create and assign tickets while viewers cannot mutate records.

## Common Pitfalls

- Register admin models in module code, but expose the model in `AppManifest.models`.
- Keep durable audit persistence out of the demo service; wire a real store before production.

## Extension Ideas

Add `AdminAuditLog`, model-backed admin users, query inspector coverage, and container/pod admin modules.

## Related APIs

`AdminIntegration`, `AdminModules`, `ModelAdmin`, `@register`, `AdminRole`, `AdminPermission`, `AppManifest`.
