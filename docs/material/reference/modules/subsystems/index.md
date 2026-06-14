# Subsystems Module

> `aquilia.subsystems` — Admin subsystem orchestration

The Subsystems module provides orchestration for the admin dashboard's modular architecture, managing admin modules, containers, monitoring, and security subsystems.

## Key Functions

`build_admin_flow_pipeline`

Constructs the flow pipeline for admin dashboard request processing, integrating authentication, authorization, and audit logging into a single composable pipeline.

## Import Path

```python
from aquilia.subsystems import AdminSubsystems, build_admin_flow_pipeline
```

## Related Modules

- [admin](../admin/index.md) — Admin dashboard that uses subsystems
- [core/flow](../core/flow.md) — Flow pipeline composition