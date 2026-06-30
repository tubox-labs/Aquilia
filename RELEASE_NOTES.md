# Aquilia v1.2.1

Release date: 2026-07-01
Release Name: "Kraken's Wake"

## Summary

Aquilia v1.2.1 is a patch release resolving critical issues around template dependency decoupling, startup performance without Jinja2 installed, and Windows-specific file locking in the trace storage engine.

## Changes

### Fixed
- **Startup decoupling**: DEC-01 Decoupled `jinja2` and `markupsafe` from core dependencies, moving them to the `aquilia[template]` extras bundle.
- **Lazy Imports**: Resolved a startup crash (`ModuleNotFoundError: No module named 'jinja2'`) by converting all eager template-related package-level imports to a module-level lazy `__getattr__` import resolution mechanism.
- **Windows File Locking**: Resolved a `PermissionError: [WinError 32]` trace storage crash on Windows by ensuring every SQLite database connection is explicitly closed in `SQLiteTraceStore`.
- **Inspector Toolbar Nonces**: Fixed JSON payload parsing in the debugging toolbar by locating the script tag end delimiter dynamically instead of assuming a fixed tag signature, preventing parser crashes when CSP nonces are present.
