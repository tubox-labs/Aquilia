# Extensibility: Interceptors, Plugins & Conditionals

Aquilia v1.3.2 adds three first-class extension points to the DI container, each gated by a `DISettings` flag so they cost nothing when unused.

---

## 1. Provider Interceptors (AOP)

Interceptors wrap a provider's **instantiation** with around-advice — logging, timing, tracing, caching — without touching the service class. Wrap any provider with `intercept()`.

```python
from aquilia.di import ProviderInterceptor, intercept, ClassProvider

class TimingInterceptor(ProviderInterceptor):
    async def around_instantiate(self, ctx, nxt):
        import time
        start = time.perf_counter()
        obj = await nxt()                    # proceed to real instantiation
        print(f"built {ctx.meta.name} in {(time.perf_counter()-start)*1e6:.1f}us")
        return obj

provider = intercept(ClassProvider(UserService, scope="app"), TimingInterceptor())
container.register(provider)
```

**Ordering.** Interceptors run first = outermost. `intercept(P, A, B)` yields the chain `A(in) → B(in) → B(out) → A(out)`. Call `nxt()` to proceed; skip it to short-circuit with your own object.

The public API — `ProviderInterceptor` (protocol), `InterceptingProvider`, `InterceptContext`, `intercept()` — is exported from `aquilia.di`. The wrapped `InterceptingProvider` mirrors the inner provider's token, scope, and tags. Wrapping with an empty interceptor list raises `DIFault` (`DI_NO_INTERCEPTORS`).

---

## 2. DI Plugins

A `DIPlugin` hooks into registry construction — auto-register a family of providers, observe every registration, or inspect built containers. Honoured during boot when `enable_plugins` is on (default).

```python
from aquilia.di import DIPlugin, register_plugin, ClassProvider

class AuditPlugin(DIPlugin):
    name = "audit"                       # stable id — re-registering replaces

    def on_registry_build(self, registry):
        # after manifests load, before the graph is built
        registry.add_provider(ClassProvider(AuditLogger, scope="app"))

    def on_provider_registered(self, container, provider):
        ...                              # fires per register() call

    def on_container_built(self, container):
        ...                              # fires once each app container is built

register_plugin(AuditPlugin())
```

**Failure isolation.** A plugin hook that raises is logged and skipped — it never crashes boot. Manage the registry with `unregister_plugin(name)`, `get_plugins()`, and `clear_plugins()` (test teardown). Plugins are deduplicated by `.name`. `get_plugins()` returns `[]` when `enable_plugins` is off.

---

## 3. Conditional Providers

Gate registration on the environment or config — the Spring `@Profile` / `@ConditionalOnProperty` equivalent. Honoured when `enable_conditional_providers` is on (default).

```python
from aquilia.di import service, conditional, ConditionContext

# via the when= parameter on @service
@service(when=lambda c: c.env == "prod")
class RealPaymentGateway: ...

@service(when=lambda c: c.env != "prod")
class FakePaymentGateway: ...

# standalone @conditional — matches prod OR staging (case-insensitive)
@conditional(lambda c: c.is_env("prod", "staging"))
class MetricsExporter: ...

# property-based: dot-path lookup into config
@conditional(lambda c: c.get("cache.backend") == "redis")
class RedisCacheWarmup: ...
```

`ConditionContext` is a frozen dataclass with two fields — `env` (the active environment, from `AQUILIA_ENV` or config) and `config` — plus two helpers: `get(path, default)` for dot-path lookups and `is_env(*names)` for case-insensitive env matching.

**Safe by default.** A service with no condition always registers. If a predicate raises, the service is skipped (treated as `False`) and boot continues — a bad predicate never crashes startup. Use `should_register(target, ctx)` to evaluate a predicate manually.
