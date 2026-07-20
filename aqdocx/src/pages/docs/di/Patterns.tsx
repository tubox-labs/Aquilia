import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { ArrowLeft, ArrowRight, Boxes } from 'lucide-react'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'

export function DIPatterns() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'
  const head = isDark ? 'text-white' : 'text-gray-900'

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      {/* Title Header */}
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Boxes className="w-4 h-4" />
          Dependency Injection / Patterns &amp; Recipes
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${head} mb-4`}>
          Patterns &amp; Real-World Recipes
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          A cookbook of production-tested DI patterns — from basic registration to large-scale application architecture. Every recipe is runnable and reflects the actual <code className="text-aquilia-500">aquilia.di</code> implementation.
        </p>
      </div>

      {/* 1. Basic registration */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>1. Basic Service Registration</h2>
        <p className={`mb-4 ${subtleText}`}>
          The idiomatic path is declarative: decorate a class with <code className="text-aquilia-500">@service</code> and list it in your module's <code className="text-aquilia-500">manifest.py</code>. The runtime discovers it, builds a <code className="text-aquilia-500">ClassProvider</code>, and wires its constructor. Scope defaults to <code className="text-aquilia-500">"app"</code>.
        </p>
        <CodeBlock language="python" filename="modules/users/services.py">{`from aquilia.di import service

@service()  # scope="app" (one instance per app container)
class GreetingService:
    def greet(self, name: str) -> str:
        return f"Hello, {name}!"`}</CodeBlock>
        <CodeBlock language="python" filename="modules/users/manifest.py">{`from aquilia.aquilary import AppManifest

manifest = AppManifest(
    name="users",
    services=["modules.users.services:GreetingService"],
    controllers=["modules.users.controllers:UsersController"],
)`}</CodeBlock>
        <p className={`mb-4 mt-4 ${subtleText}`}>
          For programmatic setup (tests, scripts) register directly against a container:
        </p>
        <CodeBlock language="python" filename="Programmatic registration">{`from aquilia.di import Container, ClassProvider

container = Container(scope="app")
container.register(ClassProvider(GreetingService, scope="app"))

svc = await container.resolve_async(GreetingService)
print(svc.greet("Ada"))  # Hello, Ada!`}</CodeBlock>
      </section>

      {/* 2. Constructor injection */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>2. Constructor Injection</h2>
        <p className={`mb-4 ${subtleText}`}>
          Aquilia reads type hints from <code className="text-aquilia-500">__init__</code> and resolves each annotated parameter. No annotation and no default raises <code className="text-aquilia-500">DIError</code> at container build; a default makes the parameter optional (skipped by DI).
        </p>
        <CodeBlock language="python" filename="Constructor wiring">{`@service()
class UserRepository:
    def __init__(self, db: Database):        # resolved by type
        self.db = db

@service()
class UserService:
    def __init__(self, repo: UserRepository, cache: CacheBackend):
        self.repo = repo
        self.cache = cache

    async def get(self, user_id: str):
        if cached := await self.cache.get(f"user:{user_id}"):
            return cached
        user = await self.repo.find(user_id)
        await self.cache.set(f"user:{user_id}", user, ttl=300)
        return user`}</CodeBlock>
        <div className="border-l-4 border-aquilia-500 bg-aquilia-500/5 pl-4 py-3 rounded-r-xl my-6">
          <p className="text-xs text-aquilia-500/90 leading-relaxed">
            <strong>Async construction:</strong> if a class defines an <code className="text-xs">async def async_init(self)</code> method, the <code className="text-xs">ClassProvider</code> calls it automatically after <code className="text-xs">__init__</code> — useful when setup needs <code className="text-xs">await</code> (connect a pool, warm a cache).
          </p>
        </div>
        <CodeBlock language="python" filename="async_init convention">{`@service(scope="app")
class SearchIndex:
    def __init__(self, config: AppConfig):
        self.config = config
        self.client = None

    async def async_init(self):
        self.client = await connect_elastic(self.config.es_url)`}</CodeBlock>
      </section>

      {/* 3. Factory providers */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>3. Factory Providers</h2>
        <p className={`mb-4 ${subtleText}`}>
          When construction needs logic — reading config, choosing an implementation, calling an async connector — use a factory. The factory's own parameters are injected too. Use <code className="text-aquilia-500">@provides(Token)</code> when the return type is abstract.
        </p>
        <CodeBlock language="python" filename="Factory + provides">{`from aquilia.di import factory, provides, FactoryProvider

# Simple factory — token is the function
@factory(scope="singleton")
async def create_http_client(config: AppConfig) -> HttpClient:
    return HttpClient(base_url=config.api_url, timeout=config.timeout)

# @provides — bind an abstract token to a concrete build
@provides(PaymentGateway, scope="app", tag="live")
def build_gateway(config: AppConfig) -> PaymentGateway:
    return StripeGateway(config.stripe_key)

# Programmatic equivalent
container.register(FactoryProvider(create_http_client, scope="singleton"))`}</CodeBlock>
      </section>

      {/* 4. Async providers & config service */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>4. Configuration Service</h2>
        <p className={`mb-4 ${subtleText}`}>
          A config object is the classic singleton: build it once, inject it everywhere. Bind a ready-made instance with <code className="text-aquilia-500">ValueProvider</code> (or <code className="text-aquilia-500">register_instance</code>) so DI hands back the same object without instantiating anything.
        </p>
        <CodeBlock language="python" filename="Config as a value provider">{`from aquilia.di import ValueProvider

@dataclass
class AppConfig:
    db_url: str
    api_url: str
    timeout: float = 30.0

config = AppConfig(db_url=env("DATABASE_URL"), api_url=env("API_URL"))

# Bind the concrete instance under the AppConfig token
container.register(ValueProvider(value=config, token=AppConfig, scope="singleton"))

# Now every service that asks for AppConfig gets this exact object
@service(scope="app")
class Mailer:
    def __init__(self, config: AppConfig):
        self.config = config`}</CodeBlock>
      </section>

      {/* 5. Repository & database pattern */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>5. Repository &amp; Database Pattern</h2>
        <p className={`mb-4 ${subtleText}`}>
          Bind an abstract repository interface to a concrete backend with <code className="text-aquilia-500">container.bind()</code>. Consumers depend on the interface, so you can swap SQL for in-memory in tests without touching call sites.
        </p>
        <CodeBlock language="python" filename="Interface → implementation">{`from abc import ABC, abstractmethod

class UserRepo(ABC):
    @abstractmethod
    async def find(self, user_id: str) -> User | None: ...

class SqlUserRepo(UserRepo):
    def __init__(self, db: Database):
        self.db = db
    async def find(self, user_id: str):
        return await self.db.fetch_one(
            "SELECT * FROM users WHERE id = $1", user_id
        )  # parameterized — never string-format SQL

# Bind interface to implementation (creates a ClassProvider internally)
container.bind(UserRepo, SqlUserRepo, scope="app")

@service()
class ProfileService:
    def __init__(self, users: UserRepo):   # gets SqlUserRepo
        self.users = users`}</CodeBlock>
      </section>

      {/* 6. Tagged providers */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>6. Tagged Providers (Multiple Implementations)</h2>
        <p className={`mb-4 ${subtleText}`}>
          When several providers satisfy one token, disambiguate with a <strong>tag</strong>. Register each under a tag, then select one at the injection site with <code className="text-aquilia-500">Inject(tag=...)</code>. Resolving an ambiguous token without a tag surfaces the mismatch.
        </p>
        <CodeBlock language="python" filename="Tagged cache backends">{`from typing import Annotated
from aquilia.di import Inject, ClassProvider

container.register(ClassProvider(RedisCache, scope="app"), tag="redis")
container.register(ClassProvider(MemoryCache, scope="app"), tag="memory")

@service()
class SessionStore:
    def __init__(
        self,
        hot:  Annotated[CacheBackend, Inject(tag="redis")],
        cold: Annotated[CacheBackend, Inject(tag="memory")],
    ):
        self.hot = hot
        self.cold = cold

# Direct resolution with a tag
redis = await container.resolve_async(CacheBackend, tag="redis")`}</CodeBlock>
      </section>

      {/* 7. Optional dependencies */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>7. Optional Dependencies</h2>
        <p className={`mb-4 ${subtleText}`}>
          Two ways to make a dependency optional. Both resolve to <code className="text-aquilia-500">None</code> when the provider is absent instead of raising <code className="text-aquilia-500">ProviderNotFoundError</code>:
        </p>
        <CodeBlock language="python" filename="Optional injection">{`from typing import Annotated, Optional
from aquilia.di import Inject

@service()
class AnalyticsService:
    def __init__(
        self,
        # (a) Optional[T] type — DI marks it optional automatically
        tracer: Optional[Tracer],
        # (b) explicit Inject(optional=True)
        metrics: Annotated[MetricsClient, Inject(optional=True)],
    ):
        self.tracer = tracer      # None if no Tracer registered
        self.metrics = metrics    # None if no MetricsClient registered

    async def record(self, event: str):
        if self.metrics:          # guard — may be None
            await self.metrics.incr(event)`}</CodeBlock>
        <p className={`mt-4 ${subtleText}`}>
          A constructor parameter with a <strong>default value</strong> is also treated as optional and skipped by DI if unresolved.
        </p>
      </section>

      {/* 8. Lazy resolution */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>8. Lazy Resolution (Breaking Cycles)</h2>
        <p className={`mb-4 ${subtleText}`}>
          Two singletons that need each other form a cycle the graph validator rejects. A <code className="text-aquilia-500">LazyProxyProvider</code> defers resolution until first attribute access, breaking the construction-time loop. Reach for it only when a redesign (extract an interface, use events) isn't practical.
        </p>
        <CodeBlock language="python" filename="Lazy proxy to break A↔B">{`from aquilia.di import LazyProxyProvider, ClassProvider

# ServiceA needs ServiceB and vice-versa.
container.register(ClassProvider(ServiceB, scope="app"))
# Register a lazy proxy for B under a distinct token A depends on:
container.register(LazyProxyProvider(token=LazyB, target_token=ServiceB))

@service()
class ServiceA:
    def __init__(self, b: LazyB):     # gets a proxy, not a live ServiceB
        self._b = b                   # ServiceB is built on first b.<attr> access`}</CodeBlock>
        <div className="border-l-4 border-yellow-500 bg-yellow-500/5 pl-4 py-3 rounded-r-xl my-6">
          <p className="text-xs text-yellow-600 dark:text-yellow-400 leading-relaxed">
            The proxy resolves synchronously on first access via a persistent per-thread event loop. It <strong>refuses to resolve inside a running event loop</strong> (would deadlock) — so the first touch must happen outside the async hot path, or you should resolve <code className="text-xs">ServiceB</code> explicitly with <code className="text-xs">await</code>.
          </p>
        </div>
      </section>

      {/* 9. Request-scoped services */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>9. Request-Scoped Services</h2>
        <p className={`mb-4 ${subtleText}`}>
          A <code className="text-aquilia-500">request</code>-scoped service lives for one HTTP request and is cached in the per-request child container. Perfect for a unit-of-work, a request-bound logger, or the current user. The ASGI layer creates and disposes the request container automatically.
        </p>
        <CodeBlock language="python" filename="Unit of work per request">{`@service(scope="request")
class UnitOfWork:
    def __init__(self, db: Database):     # db is app-scoped, shared
        self.db = db
        self.tx = None

    async def async_init(self):
        self.tx = await self.db.begin()

    async def commit(self):
        await self.tx.commit()

@service(scope="request")
class OrderService:
    def __init__(self, uow: UnitOfWork):  # same UoW for the whole request
        self.uow = uow`}</CodeBlock>
        <div className="border-l-4 border-red-500 bg-red-500/5 pl-4 py-3 rounded-r-xl my-6">
          <p className="text-xs text-red-500/90 leading-relaxed">
            <strong>Captive dependency:</strong> a <code className="text-xs">singleton</code>/<code className="text-xs">app</code> service must not inject a <code className="text-xs">request</code>-scoped one — the short-lived instance would be captured for the process lifetime. With <code className="text-xs">scope_enforcement="raise"</code> this throws <code className="text-xs">ScopeViolationError</code> at resolution.
          </p>
        </div>
      </section>

      {/* 10. Transient services */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>10. Transient &amp; Pooled Services</h2>
        <p className={`mb-4 ${subtleText}`}>
          <code className="text-aquilia-500">transient</code> builds a fresh instance on every resolve (stateless helpers, per-use builders). <code className="text-aquilia-500">pooled</code> hands out reusable instances from a bounded <code className="text-aquilia-500">asyncio.Queue</code> (heavy clients, capped concurrency).
        </p>
        <CodeBlock language="python" filename="Transient + pooled">{`from aquilia.di import PoolProvider

@service(scope="transient")
class RequestIdGenerator:      # new one every time it is injected
    def next(self) -> str:
        return uuid4().hex

# Pool of 10 heavy clients; fast-fail if 256 callers pile up
async def make_worker() -> HeavyWorker:
    return await HeavyWorker.connect()

container.register(PoolProvider(
    make_worker, max_size=10, token=HeavyWorker,
    acquire_timeout=30.0, max_waiters=256,
))

# Auto acquire/release
async with pool.acquire() as worker:
    await worker.run(job)`}</CodeBlock>
      </section>

      {/* 11. Service composition */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>11. Service Composition</h2>
        <p className={`mb-4 ${subtleText}`}>
          Compose small, single-responsibility services into higher-level ones. DI resolves the whole tree in dependency order, deduplicating shared leaves (a <code className="text-aquilia-500">Database</code> depended on by three services is built once).
        </p>
        <CodeBlock language="python" filename="Composition tree">{`@service()
class NotificationService:
    def __init__(self, mailer: Mailer, sms: SmsClient):
        self.mailer, self.sms = mailer, sms

@service()
class CheckoutService:
    def __init__(
        self,
        orders: OrderRepository,
        payments: PaymentGateway,
        notify: NotificationService,
    ):
        self.orders, self.payments, self.notify = orders, payments, notify

    async def checkout(self, cart):
        order = await self.orders.create(cart)
        await self.payments.charge(order.total)
        await self.notify.mailer.send(order.receipt())
        return order`}</CodeBlock>
      </section>

      {/* 12. Cross-app depends_on */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>12. Cross-App Dependencies (<code>depends_on</code>)</h2>
        <p className={`mb-4 ${subtleText}`}>
          In a multi-module app, one module can consume another's services — but the edge must be declared in the manifest's <code className="text-aquilia-500">depends_on</code>. The registry validates the edge statically; the runtime wires a dependency link so resolution falls through to the owning app's container.
        </p>
        <CodeBlock language="python" filename="modules/billing/manifest.py">{`manifest = AppManifest(
    name="billing",
    depends_on=["auth"],           # billing may inject auth-owned services
    services=["modules.billing.services:InvoiceService"],
)`}</CodeBlock>
        <CodeBlock language="python" filename="modules/billing/services.py">{`@service()
class InvoiceService:
    # AuthService is owned by the "auth" app; resolvable because
    # billing declares depends_on=["auth"].
    def __init__(self, auth: AuthService):
        self.auth = auth`}</CodeBlock>
        <div className="border-l-4 border-red-500 bg-red-500/5 pl-4 py-3 rounded-r-xl my-6">
          <p className="text-xs text-red-500/90 leading-relaxed">
            An undeclared cross-app dependency raises <code className="text-xs">CrossAppDependencyError</code> at boot (static validation). A cycle between app links raises <code className="text-xs">DependencyCycleError</code> at resolution instead of deadlocking. The owning app instantiates and caches its singletons exactly once.
          </p>
        </div>
      </section>

      {/* 13. Plugins / extension */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>13. Plugin / Extension Scenario</h2>
        <p className={`mb-4 ${subtleText}`}>
          A <code className="text-aquilia-500">DIPlugin</code> hooks into registry construction — auto-register a family of providers, observe every registration, or inspect built containers. Ideal for a shared library that self-wires when installed.
        </p>
        <CodeBlock language="python" filename="Auto-registering plugin">{`from aquilia.di import DIPlugin, register_plugin, ClassProvider

class AuditPlugin(DIPlugin):
    name = "audit"                 # stable id — re-registering replaces

    def on_registry_build(self, registry):
        registry.add_provider(ClassProvider(AuditLogger, scope="app"))

    def on_container_built(self, container):
        log.info("DI container ready with audit wiring")

register_plugin(AuditPlugin())     # honoured when enable_plugins=True`}</CodeBlock>
        <p className={`mt-4 ${subtleText}`}>
          Combine with a <strong>provider interceptor</strong> for around-advice on instantiation (timing, tracing) — see <Link to="/docs/di/advanced" className="text-aquilia-500 underline">Advanced DI</Link>.
        </p>
      </section>

      {/* 14. Testing & mocking */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>14. Testing &amp; Mocking</h2>
        <p className={`mb-4 ${subtleText}`}>
          Swap real services for mocks without rebuilding the container. <code className="text-aquilia-500">override_container</code> is an async context manager that force-replaces a provider for the duration of a block and restores it on exit.
        </p>
        <CodeBlock language="python" filename="test_checkout.py">{`import pytest
from unittest.mock import AsyncMock
from aquilia.di.testing import override_container

@pytest.mark.asyncio
async def test_checkout_charges_card(app_container):
    fake_gateway = AsyncMock()
    fake_gateway.charge.return_value = {"status": "ok"}

    async with override_container(app_container, PaymentGateway, fake_gateway):
        checkout = await app_container.resolve_async(CheckoutService)
        await checkout.checkout(sample_cart)
        fake_gateway.charge.assert_awaited_once()`}</CodeBlock>
        <p className={`mt-4 ${subtleText}`}>
          For whole-suite wiring use <code className="text-aquilia-500">TestRegistry</code> (relaxed: cross-app checks off, cycles tolerated) with an <code className="text-aquilia-500">overrides</code> map, or the built-in <code className="text-aquilia-500">di_container</code> / <code className="text-aquilia-500">request_container</code> pytest fixtures.
        </p>
        <CodeBlock language="python" filename="TestRegistry overrides">{`from aquilia.di import TestRegistry, MockProvider

registry = TestRegistry.from_manifests(
    manifests,
    overrides={
        "modules.billing.gateway.PaymentGateway":
            MockProvider(value=fake_gateway, token=PaymentGateway),
    },
)
container = registry.build_container()`}</CodeBlock>
      </section>

      {/* 15. Large application architecture */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>15. Large Application Architecture</h2>
        <p className={`mb-4 ${subtleText}`}>
          At scale, lean on the manifest-first model and a few conventions:
        </p>
        <div className="space-y-3 mb-6 text-sm">
          {[
            ['One app per bounded context', 'Each business domain (auth, billing, catalog) is its own module with its own manifest. Cross-context wiring is explicit via depends_on — the dependency graph is auditable.'],
            ['Depend on interfaces, not concretions', 'Bind interfaces at the composition root (manifest / bind()). Swapping an implementation is a one-line change, and tests inject fakes freely.'],
            ['Singletons for stateless infra', 'Connection pools, HTTP clients, config → app/singleton scope. Per-request state (UoW, current user) → request scope. Never capture request state in a singleton.'],
            ['Fail fast in production', 'Set scope_enforcement="raise" and strict_service_registration=True so misconfiguration aborts boot instead of degrading at runtime.'],
            ['Validate the graph in CI', 'Run aq di-check in your pipeline to catch missing providers, cycles, and undeclared cross-app edges before deploy.'],
          ].map(([title, desc], i) => (
            <div key={i} className="flex gap-3">
              <span className="mt-1.5 w-2 h-2 rounded-full bg-aquilia-500 shrink-0" />
              <span><strong className={head}>{title}.</strong> <span className={subtleText}>{desc}</span></span>
            </div>
          ))}
        </div>
        <CodeBlock language="python" filename="Production di config (workspace.py)">{`class ProdEnv(BaseEnv):
    class di(BaseEnv.di):
        scope_enforcement           = "raise"   # captive deps abort boot
        strict_service_registration = True      # a bad service fails fast
        parallel_resolution         = True      # concurrent independent deps
        pool_max_waiters            = 256`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`mt-16 pt-8 border-t flex justify-between ${isDark ? 'border-white/5' : 'border-gray-200'}`}>
        <Link to="/docs/di/advanced" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition font-medium">
          <ArrowLeft className="w-4 h-4" /> Advanced
        </Link>
        <Link to="/docs/di/troubleshooting" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition font-medium">
          Errors &amp; Troubleshooting <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
