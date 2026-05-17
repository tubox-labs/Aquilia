# Reference Suite

The reference suite complements the app starters with executable subsystem examples. Each script uses real Aquilia APIs and avoids external services by using memory, temporary filesystem, mock transport, or sqlite-backed resources.

Run everything:

```bash
python -m examples.reference_suite.run_all
```

Run through pytest:

```bash
python -m pytest examples/reference_suite -q
```

## Covered APIs

| Script | APIs exercised |
| --- | --- |
| `core_config_runtime.py` | `Workspace`, `Module`, `Integration`, `AquilaConfig`, `Env`, `ConfigLoader`, `RuntimeConfig`, `AquiliaRuntime`, `AppManifest`, controller decorators |
| `dependency_injection.py` | `Container`, `ValueProvider`, `ClassProvider`, request scopes, async resolution, shutdown |
| `cache_storage_filesystem.py` | `CacheService`, `MemoryBackend`, cache stats, `MemoryStorage`, native filesystem helpers |
| `sqlite_models.py` | `aquilia.sqlite.create_pool`, transactions, `Model` field declarations |
| `i18n_templates_mail.py` | `MemoryCatalog`, `I18nService`, `TemplateLoader`, `TemplateEngine`, `MailEnvelope`, `ConsoleProvider` |
| `artifacts_signing_versioning.py` | `ArtifactBuilder`, `MemoryArtifactStore`, `ArtifactReader`, `Signer`, signed JSON payloads, `ApiVersion`, resolvers |
| `http_patterns_faults.py` | `AsyncHTTPClient`, `MockTransport`, `compile_pattern`, `PatternMatcher`, `FaultEngine` |

These scripts are intentionally small enough to inspect, but they are not pseudo-code: they are imported by tests and execute against the local framework implementation.
