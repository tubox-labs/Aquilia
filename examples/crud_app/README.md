# CRUD App Starter

This starter is a project tracker with create, read, update, archive, and restore flows. It includes an Aquilia model for the persistent shape, blueprints for request contracts, a repository-style service, controller routes, and tests for the business layer.

The repository uses memory so the example has no setup step. Replace `ProjectRepository` with a model-backed implementation when you connect `Workspace.database()` to a real database.
