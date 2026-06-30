# Aquilia v1.2.0

Release date: 2026-06-28
Release Name: "Kraken's Wake"

## Summary

Aquilia v1.2.0 brings major feature additions, optimizations, and compatibility improvements across database migrations, CLI help formatting, localized manifest versioning configurations, cross-field validation, transformation pipelines, columnar validation, discriminated unions, and a brand-new execution tracer in the request inspector toolbar.

## Changes

### Added
- **Request Inspector** (`aquilia.inspector`): Full per-request execution tracing with swimlane-based timeline visualization, SSE live streaming, profile profiling support (`X-Profile: true`), redaction rules, and cookie redirect folding.
- **Database CLI Subcommands**: Added `aq db history`, `aq db rollback`, `aq db check`, `aq db diff`, `aq db seed`, `aq db reset`, and `aq db flush`.
- **Click CLI Help Custom Colorization**: Options colored in bold green, help text in white, and headers in bold cyan.
- **Manifest-Level API Versioning Override**: Replaced legacy `Module().versioning()` builder API with a new `AppManifest.versioning` property configured directly in `manifest.py`.
- **Advanced Validation Engines**: Cross-field validation (`@ward`), facets chaining pipelines (`>>`), columnar validation (`seal_columnar`), discriminated unions (`BlueprintUnion`), form/file blueprint validation (`UploadFile`), and `Sigil` intermediate schema representation.

### Removed
- **Artifact System**: Entirely removed `aquilia.artifacts` module (`ws.surp` artifacts, etc.), and `compile` and `freeze` commands from the CLI.

### Changed & Optimized
- **SQLite Adapter**: sqlite Row objects inherit from dict, avoiding conversion loops.
- **Runtime Performance**: Optimized DI container registration, header decoded caches, lazy wrapping in DataObject, and regex compilation caching in `sigil.py`.

### Fixed
- **OS Compatibility**: Graceful Windows compatibility handling in MCP daemon processes and process signals.
- **Stability**: Multiple bug fixes in auto-discovery namespace preservation, PEP 563 / PEP 604 string annotations, and Request ID propagation.

## Verification

- Python import checks passed.
- Ruff source lint and format checks passed.
- Full test suite execution: 6507 passed, 1 skipped.
