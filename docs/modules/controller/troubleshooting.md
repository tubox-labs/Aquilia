# Controllers Troubleshooting

## First Checks

1. Confirm the module is registered in `workspace.py` when it is application-facing.
2. Confirm the component is declared in `modules/<name>/manifest.py` when it is a controller, service, model, task, middleware, or socket controller.
3. Confirm configuration dataclasses or integration objects serialize with the values you expect by inspecting `workspace.to_dict()`.
4. Confirm imports point at real `module.path:ClassName` strings.
5. Run focused tests for the subsystem and read the fault metadata when one is raised.

## Common Symptoms

| Symptom | Likely Cause | What To Check |
| --- | --- | --- |
| Component is not found | Manifest path is wrong or module was not discovered | `AppManifest` component lists and workspace module name |
| Runtime starts but route or handler is missing | Controller decorator metadata did not compile or route prefix differs | Controller `prefix`, route decorators, `Module.route_prefix()` |
| Config appears ignored | Value is in manifest when runtime expects workspace integration, or the integration key differs | `configuration.md` and `workspace.to_dict()` |
| State disappears between requests | In-memory backend or request-scoped object was used for durable state | Backend choice and DI scope |
| Fault response is too generic | Raw exception escaped or fault handler mapping is missing | Fault type, fault engine debug mode, middleware order |

## Diagnostic Snippets

```python
# Inspect effective workspace config
import workspace
print(workspace.workspace.to_dict())
```

```python
# Check public API availability
import aquilia.controller
```

## Escalation Path

If a behavior is unclear, inspect the source file listed beside the class or function in `api-reference.md`, then search `tests/` for the class name. The repository tests are the best source for edge-case behavior.
