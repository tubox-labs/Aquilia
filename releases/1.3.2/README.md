# Aquilia v1.3.2 Release Notes — "Deep Current"

Aquilia v1.3.2 is a ground-up rewrite of the dependency-injection subsystem (`aquilia.di`). It unifies two parallel resolution engines into one, surfaces every container knob through a single typed configuration block, and adds three enterprise extension points — provider interceptors, DI plugins, and conditional providers — while hardening pooling, sync bridging, and cross-app resolution. The public API stays backward compatible: existing `@service`, `Dep()`, and `Container` code runs unchanged.

## Table of Contents

1. [DI Settings & Configuration](di-settings.md)
   * The new typed `DISettings` object and the `AquilaConfig.DI` config block.
   * Scope enforcement, parallel resolution, diagnostics, disposal, and pooling knobs.
   * `configure_di`, `get_di_settings`, `reset_di_settings`, and `DIConfigFault`.
2. [Unified Resolution Engine](engine.md)
   * Folding `RequestDAG` into the container — one engine for the whole framework.
   * Sub-dependency dedup, parallel branches, generator teardown, cross-link cycle detection.
   * New `Container` methods: `add_dependency_link`, `create_child`, `replace_provider`, `resolve_dep`.
3. [Extensibility: Interceptors, Plugins & Conditionals](extensibility.md)
   * Provider interceptors (`ProviderInterceptor`, `intercept`) for instantiation around-advice.
   * DI plugins (`DIPlugin`, `register_plugin`) for registry-build hooks.
   * Conditional providers (`@service(when=...)`, `@conditional`, `ConditionContext`).
4. [Migration Guide](migration.md)
   * Deprecations: `ServiceScope` Enum, `clear_request_container`, `ModuleContainer` removal.
   * Environment-flag → `DISettings` configuration.
   * Behavioral changes and how to adopt them.

---

## Key Goals

1. **One Engine**: Collapse the container resolver and the FastAPI-`Depends`-style `RequestDAG` into a single engine owned by the container, so inline `Dep()` dependencies and constructor-injected services share one deduplicated graph.
2. **Typed Configuration**: Replace loose `os.environ` flags with an immutable, validated `DISettings` object, configured through `workspace.py` like every other subsystem. Bad configuration fails fast at boot with `DIConfigFault`.
3. **Extensibility**: Add first-class AOP (interceptors), registry-build hooks (plugins), and environment/feature-gated registration (conditional providers) — the Spring `@Profile` / `@ConditionalOnProperty` equivalent.
4. **Production Hardening**: Persistent per-thread sync loop (no throwaway loop per call), bounded pool waiters (fast-fail under overload), in-flight dedup for concurrent resolvers, and cross-app cycle detection that raises instead of deadlocking.
5. **Structured Faults**: Every DI failure raises a `DIFault` subclass with a stable code — never a bare `ValueError`/`RuntimeError` — so the Fault Engine renders them consistently.
