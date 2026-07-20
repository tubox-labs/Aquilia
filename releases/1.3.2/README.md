# Aquilia v1.3.2 Release Notes — "Specula API Observatory & Deep Current"

Aquilia v1.3.2 is a major release introducing **Specula** (a compiled, introspective ASGI dashboard and API exploration subsystem replacing legacy OpenAPI) alongside a ground-up rewrite of the dependency-injection subsystem (`aquilia.di`).

---

## Table of Contents

### Specula API Observatory
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

### Dependency Injection Subsystem ("Deep Current")
5. [DI Settings & Configuration](di-settings.md)
   * The new typed `DISettings` object and the `AquilaConfig.DI` config block.
   * Scope enforcement, parallel resolution, diagnostics, disposal, and pooling knobs.
   * `configure_di`, `get_di_settings`, `reset_di_settings`, and `DIConfigFault`.
6. [Unified Resolution Engine](engine.md)
   * Folding `RequestDAG` into the container — one engine for the whole framework.
   * Sub-dependency dedup, parallel branches, generator teardown, cross-link cycle detection.
   * New `Container` methods: `add_dependency_link`, `create_child`, `replace_provider`, `resolve_dep`.
7. [Extensibility: Interceptors, Plugins & Conditionals](extensibility.md)
   * Provider interceptors (`ProviderInterceptor`, `intercept`) for instantiation around-advice.
   * DI plugins (`DIPlugin`, `register_plugin`) for registry-build hooks.
   * Conditional providers (`@service(when=...)`, `@conditional`, `ConditionContext`).

### Migration Guide
8. [Migration Guide](migration.md)
   * OpenAPI to Specula migration.
   * DI settings, deprecations, and behavioral changes.

---

## Key Subsystem Improvements

### Specula API Observatory
1. **Compilation over Code Scanning**: No more parsing source files or class matching at runtime. Specula extracts endpoint specs directly from Aquilia's compiled in-memory ASGI routing topology.
2. **Developer Reactivity**: Hot-reloading modules push Specula spec invalidations down active Server-Sent Events (SSE) connections, immediately refreshing the developer's dashboard.
3. **Simulated Sandbox**: Frontends can start testing integration before the backend endpoints are written. The mock server synthesizes response payloads matching the exact JSON schemas defined in Contracts or ORM Models.
4. **Complete Security Transparency**: Exposes exact pipeline guards, role requirements, and AccessLevel clearance levels to ensure complete architectural observability.

### Dependency Injection Rewrite
1. **One Engine**: Collapse the container resolver and the FastAPI-`Depends`-style `RequestDAG` into a single engine owned by the container, so inline `Dep()` dependencies and constructor-injected services share one deduplicated graph.
2. **Typed Configuration**: Replace loose `os.environ` flags with an immutable, validated `DISettings` object, configured through `workspace.py` like every other subsystem. Bad configuration fails fast at boot with `DIConfigFault`.
3. **Extensibility**: Add first-class AOP (interceptors), registry-build hooks (plugins), and environment/feature-gated registration (conditional providers) — the Spring `@Profile` / `@ConditionalOnProperty` equivalent.
4. **Production Hardening**: Persistent per-thread sync loop (no throwaway loop per call), bounded pool waiters (fast-fail under overload), in-flight dedup for concurrent resolvers, and cross-app cycle detection that raises instead of deadlocking.
5. **Structured Faults**: Every DI failure raises a `DIFault` subclass with a stable code — never a bare `ValueError`/`RuntimeError` — so the Fault Engine renders them consistently.
