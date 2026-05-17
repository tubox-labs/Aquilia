# Documentation Coverage Report

This report was produced after the read-only audit and documents the rebuilt markdown set.

## Source Audit

- Python files parsed under `aquilia/`: 540
- Package modules documented: 35 including synthetic `core`
- Root core files grouped under `core`: 22
- Mounted Click command/group objects inspected: 129

## Rebuilt Documentation

Each module now has `README.md`, `architecture.md`, `configuration.md`, `api-reference.md`, `integration-guide.md`, `cli-reference.md`, `examples.md`, `edge-cases-and-limitations.md`, and `troubleshooting.md`.

Top-level guides include installation, configuration, full CLI reference, runtime lifecycle, developer guide, examples, operations/security, module index, and this coverage report.

## Known Documentation Boundaries

- API references are AST-derived and focus on public classes/functions/methods plus constants and exports. Private helper bodies are not reproduced line-by-line.
- Command references are Click-derived and document mounted `aq` commands. Module-local helper CLIs that are not mounted are called out as such.
- Examples use checked repository examples and public APIs visible in source; they avoid inventing project-specific behavior.

## Modules Covered

| Module | Files | Lines | Classes | Functions | Commands Mapped |
| --- | ---: | ---: | ---: | ---: | ---: |
| `core` | 22 | 27322 | 132 | 46 | 12 |
| `admin` | 21 | 26075 | 92 | 53 | 8 |
| `aquilary` | 10 | 4676 | 29 | 9 | 12 |
| `artifacts` | 6 | 1859 | 19 | 2 | 11 |
| `auth` | 24 | 12774 | 164 | 61 | 0 |
| `blueprints` | 9 | 4728 | 41 | 10 | 0 |
| `cache` | 14 | 3813 | 27 | 10 | 4 |
| `cli` | 42 | 23184 | 25 | 216 | 104 |
| `controller` | 12 | 7813 | 48 | 10 | 0 |
| `db` | 9 | 3266 | 15 | 4 | 8 |
| `debug` | 2 | 1300 | 1 | 4 | 0 |
| `di` | 14 | 4800 | 44 | 16 | 0 |
| `discovery` | 2 | 747 | 9 | 0 | 1 |
| `faults` | 12 | 4801 | 127 | 23 | 0 |
| `filesystem` | 14 | 4317 | 25 | 22 | 0 |
| `http` | 17 | 8549 | 100 | 23 | 0 |
| `i18n` | 11 | 4190 | 28 | 26 | 6 |
| `integrations` | 21 | 2978 | 42 | 0 | 0 |
| `mail` | 14 | 4599 | 41 | 9 | 3 |
| `middleware_ext` | 8 | 3274 | 22 | 7 | 0 |
| `mlops` | 76 | 15885 | 212 | 30 | 24 |
| `models` | 33 | 17845 | 222 | 23 | 8 |
| `patterns` | 21 | 3246 | 35 | 18 | 0 |
| `providers` | 11 | 5882 | 72 | 0 | 16 |
| `sessions` | 9 | 3159 | 41 | 3 | 0 |
| `sockets` | 14 | 3687 | 41 | 18 | 5 |
| `sqlite` | 14 | 2672 | 20 | 8 | 8 |
| `storage` | 14 | 3166 | 28 | 2 | 0 |
| `subsystems` | 3 | 563 | 4 | 0 | 0 |
| `tasks` | 7 | 1802 | 15 | 6 | 0 |
| `templates` | 15 | 4409 | 32 | 35 | 0 |
| `testing` | 14 | 3874 | 25 | 30 | 1 |
| `typing` | 10 | 593 | 37 | 0 | 0 |
| `utils` | 4 | 326 | 2 | 2 | 0 |
| `versioning` | 11 | 2844 | 30 | 3 | 0 |
