# Aquilia v1.3.2 Release Notes — "Specula API Observatory"

Aquilia v1.3.2 introduces **Specula**, a major evolution of the framework's documentation and API exploration subsystem. Specula completely replaces the legacy OpenAPI 3.1.0 generator and static Swagger/ReDoc pages with a compiled, introspective ASGI dashboard (the Specula Observatory), reactive hot-reloading streams, automated security and clearance level mapping, a schema-synthesized mock server, and Postman/Insomnia collection exporters.

## Table of Contents

1. [Specula Observatory UI & Integration](observatory.md)
   * The new dashboard philosophy.
   * Integrating Specula via `Integration.specula(...)`.
   * UI branding and Server-Sent Events (SSE) live streams.
2. [Spec Compilation & Schema Inference](compilation.md)
   * The compiler-integrated `SpeculaBuilder`.
   * Python-to-JSON Schema type mapping.
   * Multi-strategy request body and response resolution.
3. [Automated Security & Clearance Detection](security.md)
   * Inferred security schemes from pipeline guards.
   * Integrated authorization clearance level detection.
   * Extended metadata (`x-specula-security`) vendor extensions.
4. [Mock Server & Collection Exports](mock_exports.md)
   * Interactive mocking engine at `/specula/mock`.
   * Schema synthesis with configurable recursion depth limits.
   * Dynamic exports for Postman v2.1 and Insomnia v4.
5. [Migration Guide](migration.md)
   * Removing legacy `OpenAPIIntegration` references.
   * Replaced classes, paths, and deprecations.

---

## Key Subsystem Improvements

1. **Compilation over Code Scanning**: No more parsing source files or class matching at runtime. Specula extracts endpoint specs directly from Aquilia's compiled in-memory ASGI routing topology.
2. **Developer Reactivity**: Hot-reloading modules push Specula spec invalidations down active Server-Sent Events (SSE) connections, immediately refreshing the developer's dashboard.
3. **Simulated Sandbox**: Frontends can start testing integration before the backend endpoints are written. The mock server synthesizes response payloads matching the exact JSON schemas defined in Contracts or ORM Models.
4. **Complete Security Transparency**: Exposes exact pipeline guards, role requirements, and AccessLevel clearance levels to ensure complete architectural observability.
