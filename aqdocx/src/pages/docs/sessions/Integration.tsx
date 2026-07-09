import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Cog, Database, User, Shield, Layers } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function SessionsIntegration() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const sectionHeaderClass = `text-2xl font-mono font-bold tracking-tight mb-6 flex items-center gap-3 ${
    isDark ? 'text-white' : 'text-gray-900'
  }`
  const textClass = `text-sm leading-relaxed mb-6 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-12 border-b border-zinc-200 dark:border-zinc-800 pb-8">
        <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-widest text-aquilia-500 mb-4">
          <Cog className="w-4 h-4" />
          Sessions / Workspace &amp; Manifest Integration
        </div>
        <h1 className={`text-4xl font-mono ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          <span className="font-bold tracking-tighter gradient-text relative group inline-block">
            Workspace &amp; Manifest Integration
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-zinc-300' : 'text-zinc-700'}`}>
          Configure session policies globally on the Workspace builder, override parameters locally at the module manifest level, and inject resolved session states into application services.
        </p>
      </div>

      {/* Workspace-Level Configuration */}
      <section className="mb-16">
        <h2 className={sectionHeaderClass}>
          <Database className="w-5 h-5 text-aquilia-500" />
          1. Workspace-Level Configuration
        </h2>
        <p className={textClass}>
          Enable and configure sessions globally on the <code className="text-aquilia-500">Workspace</code> builder in <code className="text-aquilia-500">workspace.py</code>.
          This constructs the central <DocTerm id="sessions.engine">SessionEngine</DocTerm> and binds it to the server's HTTP middleware stack.
        </p>
        <CodeBlock language="python" filename="workspace.py" highlightLines={[1, 10, 19, 23, 27]}>{`from datetime import timedelta
from aquilia import Workspace
from aquilia.sessions import SessionPolicy, PersistencePolicy, ConcurrencyPolicy, TransportPolicy

# Configure global workspace policies
workspace = (
    Workspace("my-app")
    .sessions(
        policies=[
            SessionPolicy(
                name="default",
                ttl=timedelta(days=7),
                idle_timeout=timedelta(hours=1),
                absolute_timeout=timedelta(days=30),
                rotate_on_use=False,
                rotate_on_privilege_change=True,
                fingerprint_binding=False,
                scope="user",
                persistence=PersistencePolicy(
                    enabled=True,
                    store_name="default",
                    write_through=True,
                    compress=False,
                ),
                concurrency=ConcurrencyPolicy(
                    max_sessions_per_principal=5,
                    behavior_on_limit="evict_oldest",
                ),
                transport=TransportPolicy(
                    cookie_name="workspace_session",
                    cookie_secure=False,
                    cookie_httponly=True,
                    cookie_samesite="lax",
                ),
            ),
        ],
    )
    .build()
)`}</CodeBlock>
      </section>

      {/* Manifest-Level Configuration */}
      <section className="mb-16 border-t border-zinc-200 dark:border-zinc-800 pt-12">
        <h2 className={sectionHeaderClass}>
          <Layers className="w-5 h-5 text-aquilia-500" />
          2. Manifest-Level Configuration
        </h2>
        <p className={textClass}>
          For isolated modules that need specific session parameters (such as shorter timeouts for payment modules or header-based transports for API domains),
          you can override configurations in the module's <code className="text-aquilia-500">manifest.py</code> file using the real <code className="text-aquilia-500">SessionConfig</code> dataclass from <code className="text-aquilia-500">aquilia.manifest</code>.
        </p>
        <CodeBlock language="python" filename="manifest.py" highlightLines={[3, 13, 23, 27]}>{`from datetime import timedelta
from aquilia import AppManifest
from aquilia.manifest import SessionConfig


manifest = AppManifest(
    name="payment_gateway",
    version="1.0.0",
    description="Secure payment operations",
    controllers=["modules.payment_gateway.controllers:PaymentController"],
    services=["modules.payment_gateway.services:TransactionService"],
    
    # Module-level session config overrides
    sessions=[
        SessionConfig(
            name="payment_session",
            enabled=True,
            ttl=timedelta(minutes=15),        # Short TTL for security
            idle_timeout=timedelta(minutes=5), # Aggressive inactivity timeout
            
            # Transport override
            transport="cookie",
            cookie_name="pay_sess_id",
            cookie_secure=True,
            cookie_httponly=True,
            cookie_samesite="Strict",
            
            # Storage and encryption
            store="memory",
            encryption_enabled=True,
            encryption_key_env="PAYMENT_SESSION_KEY",
            serializer="json",
            
            # Observability hooks
            log_lifecycle=True,
            metrics_enabled=True,
        )
    ]
)`}</CodeBlock>
      </section>

      {/* Dependency Injection Integration */}
      <section className="mb-16 border-t border-zinc-200 dark:border-zinc-800 pt-12">
        <h2 className={sectionHeaderClass}>
          <User className="w-5 h-5 text-aquilia-500" />
          3. Constructor Dependency Injection
        </h2>
        <p className={textClass}>
          At request time, the session is registered in the request-scoped DI container. Any class with request scope can automatically accept <code className="text-aquilia-500">Session</code> inside its constructor:
        </p>

        <div className={`pl-4 border-l-2 border-aquilia-500 py-1 my-6 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          <p className="text-sm font-semibold text-aquilia-500 mb-1">Note</p>
          <p className="text-sm leading-relaxed">
            Injecting <code className="text-aquilia-500">Session</code> is only supported in request-scoped components. Singleton services attempting to resolve sessions will raise dependency resolution errors.
          </p>
        </div>

        <h3 className={`text-lg font-bold font-mono mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Step 1: Service Constructor Injection
        </h3>
        <CodeBlock language="python" filename="services.py" highlightLines={[6, 9]}>{`from aquilia.di import Inject
from aquilia.sessions import Session

# CheckoutService runs in request scope
class CheckoutService:
    def __init__(self, session: Session):
        self.session = session

    async def add_discount_code(self, code: str) -> float:
        cart = self.session.get("cart", [])
        if not cart:
            return 0.0
            
        self.session["discount_code"] = code # Auto-tracked as dirty
        subtotal = sum(item["price"] for item in cart)
        return subtotal * 0.9`}</CodeBlock>

        <h3 className={`text-lg font-bold font-mono mt-8 mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Step 2: Inject Service into Controller
        </h3>
        <CodeBlock language="python" filename="controllers.py" highlightLines={[11, 14, 15]}>{`from aquilia import Controller, Post
from aquilia.sessions import session
from .services import CheckoutService


class CheckoutController(Controller):
    prefix = "/checkout"

    # Inject request-scoped CheckoutService
    def __init__(self, checkout_service: CheckoutService):
        self.checkout_service = checkout_service

    # Require a session to ensure the container can resolve the dependency
    @Post("/discount")
    @session.require()
    async def apply_discount(self, ctx):
        body = await ctx.request.json()
        code = body.get("code")
        
        # CheckoutService modifies session data directly
        new_total = await self.checkout_service.add_discount_code(code)
        
        return ctx.json({"new_total": new_total})`}</CodeBlock>
      </section>

      {/* Session Scope Lifecycle Flow */}
      <section className="mb-16 border-t border-zinc-200 dark:border-zinc-800 pt-12">
        <h2 className={sectionHeaderClass}>
          <Shield className="w-5 h-5 text-aquilia-500" />
          Request Lifecycle Execution Flow
        </h2>
        <p className={textClass}>
          The interaction between configurations, manifests, middleware, and DI occurs in a structured flow:
        </p>
        <div className="space-y-4">
          {[
            { step: '1', title: 'Initialization', desc: 'At server boot, ConfigLoader reads workspace.sessions config and manifest.py overrides, compiling the SessionEngine.' },
            { step: '2', title: 'Middleware Assembly', desc: 'The server attaches SessionMiddleware. Incoming HTTP request triggers the middleware resolver.' },
            { step: '3', title: 'DI Scoping', desc: 'A new request-scoped DI container is created. The resolved Session object is registered as a request-scoped instance.' },
            { step: '4', title: 'Dependency Resolution', desc: 'When the controller is resolved, the DI system instantiates CheckoutService, injecting the active Session.' },
            { step: '5', title: 'Commit and Save', desc: 'The handler finishes. SessionMiddleware checks for changes, persists dirty sessions to the store, and updates response headers.' },
          ].map((item, i) => (
            <div key={i} className="flex gap-4 items-start">
              <div className="w-6 h-6 rounded-full bg-aquilia-500/10 text-aquilia-500 font-bold text-xs flex items-center justify-center shrink-0">
                {item.step}
              </div>
              <div>
                <h4 className={`font-mono text-sm font-semibold ${isDark ? 'text-white' : 'text-gray-900'} mb-1`}>{item.title}</h4>
                <p className={`text-xs ${isDark ? 'text-zinc-400' : 'text-zinc-500'}`}>{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <NextSteps />
    </div>
  )
}
