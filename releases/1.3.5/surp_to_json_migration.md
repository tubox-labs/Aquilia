# SURP Binary Format Removal & JSON Standardization (v1.3.5)

## Overview

In Aquilia v1.3.5, the legacy `surp` binary serialization format and library dependency have been completely removed across the entire framework in favor of native, standardized `json` format (`.json` artifacts, `JSONBytecodeCache`, `JSONCatalog`, `JSONAuditStore`, `schema_snapshot.json`, `credentials.json`, `ws.json`, `discovery_cache.json`).

---

## Key Changes

1. **HTTP Core Layer**:
   - `Request` no longer has `is_surp()`, `accepts_surp()`, `prefers_surp()`, or `surp()` methods. `request.data()` returns `request.json()`.
   - `Response` no longer has `Response.surp()` or `@requires_surp` decorator. `Response.negotiated()` defaults to JSON encoding.
   - Removed `InvalidSurp` and `SurpUnavailable` fault classes.

2. **Internationalization (i18n)**:
   - `SurpCatalog` and `has_surp()` removed.
   - `JSONCatalog` is the default file catalog backend.
   - Default `catalog_format` in `I18nConfig` is `"json"`.

3. **Template Engine**:
   - `SurpBytecodeCache` renamed to `JSONBytecodeCache`.
   - Template compilation artifacts default to `artifacts/templates.json` with envelope `"__format__": "json"`.

4. **Aquilary & Auto-Discovery**:
   - Manifest exports and imports use `.json` format (`frozen.json`).
   - Discovery cache stored at `.aquilia/discovery_cache.json`.

5. **Models & Database**:
   - Migration DSL snapshots use `schema_snapshot.json`.
   - Migration CLI commands default `--format` option to `"json"`.

6. **Admin Audit Trail & Providers**:
   - Audit store updated to `JSONAuditStore` saving to `.aquilia/audit.json`.
   - Provider credential storage updated to `credentials.json`.

7. **Build & CI**:
   - Removed `surp` optional dependency from `pyproject.toml`, `setup.py`, and CI workflows.

---

## Migration Steps for Applications

- **File Extensions**: Rename any `.surp` configuration or manifest files in your project workspace to `.json`.
- **API Calls**: Replace any calls to `request.surp()` or `Response.surp()` with `request.json()` or `Response.json()`. Remove `@requires_surp` decorators from controller routes.
- **Imports**: Replace imports of `SurpCatalog` or `SurpBytecodeCache` with `JSONCatalog` and `JSONBytecodeCache`.
