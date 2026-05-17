# Aquilia v1.0.4

Release date: 2026-05-17

## Summary

Aquilia v1.0.4 removes the React-style workspace build system and returns the framework to a native Python backend runtime model.

## Changes

- Removed `aquilia/build` and the `aq build` command.
- Removed build checks from `aq run`, `aq serve`, and `aq deploy`.
- Removed the Admin Build page and related configuration/permission surface.
- Kept `aq compile` as an explicit artifact generation tool backed by `WorkspaceCompiler`.
- Updated `aq freeze` to create an artifact integrity snapshot under `artifacts/`.
- Updated docs and generated deployment Makefiles for the native runtime flow.
- Fixed SQLite `:memory:` pool isolation so independent pools no longer share tables.

## Verification

- Python import checks passed.
- Source lint and format checks passed for touched runtime files.
- Targeted regression/admin tests: 808 passed, 1 skipped.
- SQLite shared-memory tests: 5 passed.
- Full test suite: 6539 passed, 1 skipped.
- Package build succeeded for sdist and wheel.
- `twine check dist/*` passed.
