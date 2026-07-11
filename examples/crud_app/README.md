# CRUD App Starter

## Purpose

Project tracker showing create, read, update, archive, and restore flows with a production-shaped service boundary.

## Architecture

- `workspace.py` configures a sqlite database URL and registers the `projects` module at `/projects`.
- `models.py` declares the persistent `Project` shape using Aquilia model fields.
- `services.py` uses an in-memory repository to keep local execution dependency-free.
- `controllers.py` validates request bodies with contracts before calling the service.

## Run

```bash
cd examples/crud_app
python -m uvicorn runtime:app --reload --port 8010
```

Expected behavior: CRUD endpoints mutate the in-memory project repository and return JSON records.

## Test

```bash
python -m pytest examples/crud_app -q
```

## Common Pitfalls

- The `Project` model demonstrates the schema, but the starter service intentionally uses memory.
- Project keys are normalized to uppercase by the create contract.
- Archive is implemented as a soft state change, not a hard delete.

## Extension Ideas

Replace `ProjectRepository` with an Aquilia database-backed repository, add `aq db makemigrations`, add optimistic concurrency, and emit task notifications after archive/restore.

## Related APIs

`Model`, field classes, `Workspace.database`, `AppManifest.models`, `Contract`, `Controller`, `Response`, `ConflictFault`, `NotFoundFault`.
