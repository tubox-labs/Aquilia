import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Tag } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function SessionsDecorators() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Tag className="w-4 h-4" />
          Sessions / Decorators
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Session Decorators
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The session decorator API provides DI-integrated decorators that automatically resolve, validate, and inject sessions into controller handlers. The <code className="text-aquilia-500">session</code> singleton exposes <code className="text-aquilia-500">.require()</code>, <code className="text-aquilia-500">.ensure()</code>, and <code className="text-aquilia-500">.optional()</code> methods, plus the standalone <code className="text-aquilia-500">@authenticated</code> and <code className="text-aquilia-500">@stateful</code> decorators.
        </p>
      </div>

      {/* session.require() */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>session.require()</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Requires an existing session to be present. Raises <code className="text-aquilia-500">SessionRequiredFault</code> (HTTP 401) if no valid session is found. The session is <strong>not</strong> created automatically.
        </p>
        <CodeBlock language="python" filename="require.py">{`from aquilia import Controller, Get, Post
from aquilia.sessions import session, Session


class DashboardController(Controller):
    prefix = "/dashboard"

    @Get("/")
    @session.require()
    async def index(self, ctx, session: Session):
        """Only accessible with an existing session."""
        return ctx.json({
            "user": session.principal.id,
            "theme": session.get("theme", "light"),
        })

    @Get("/admin")
    @session.require(authenticated=True)
    async def admin(self, ctx, session: Session):
        """Requires session AND authentication.
        Raises AuthenticationRequiredFault if session exists but is not authenticated.
        """
        return ctx.json({"admin": True, "user": session.principal.id})

    @Get("/api-data")
    @session.require(policy="api")
    async def api_data(self, ctx, session: Session):
        """Use a specific session policy for this endpoint."""
        return ctx.json({"data": session.get("api_cache", {})})`}</CodeBlock>
      </section>

      {/* session.ensure() */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>session.ensure()</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Loads an existing session or creates a new one if none exists. Never fails — the handler always receives a valid session.
        </p>
        <CodeBlock language="python" filename="ensure.py">{`from aquilia import Controller, Get, Post
from aquilia.sessions import session, Session


class CartController(Controller):
    prefix = "/cart"

    @Get("/")
    @session.ensure()
    async def view_cart(self, ctx, session: Session):
        """Works for both new and returning visitors."""
        return ctx.json({"items": session.get("cart", [])})

    @Post("/add")
    @session.ensure()
    async def add_to_cart(self, ctx, session: Session):
        """Creates a session on first add, reuses on subsequent."""
        body = await ctx.json_body()
        cart = session.get("cart", [])
        cart.append(body)
        session["cart"] = cart
        return ctx.json({"items": cart}, status=201)

    @Post("/preferences")
    @session.ensure(policy="web")
    async def save_prefs(self, ctx, session: Session):
        """Use a specific policy for this endpoint."""
        body = await ctx.json_body()
        session["preferences"] = body
        return ctx.json({"saved": True})`}</CodeBlock>
      </section>

      {/* session.optional() */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>session.optional()</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Loads an existing session if present but does <strong>not</strong> create one. The session parameter may be <code className="text-aquilia-500">None</code>.
        </p>
        <CodeBlock language="python" filename="optional.py">{`from aquilia import Controller, Get
from aquilia.sessions import session, Session
from typing import Optional


class ProductController(Controller):
    prefix = "/products"

    @Get("/:id")
    @session.optional()
    async def show(self, ctx, id: str, session: Optional[Session]):
        """Session may or may not exist."""
        product = await Product.objects.get(id=id)
        
        # Personalize if session exists
        theme = "light"
        if session:
            theme = session.get("theme", "light")
            # Track recently viewed
            viewed = session.get("recently_viewed", [])
            viewed.append(id)
            session["recently_viewed"] = viewed[-10:]  # Keep last 10
        
        return ctx.json({"product": product.to_dict(), "theme": theme})`}</CodeBlock>
      </section>

      {/* @authenticated */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>@authenticated</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Shorthand decorator that requires a session with an authenticated principal. Automatically extracts the <code className="text-aquilia-500">SessionPrincipal</code> for the handler:
        </p>
        <CodeBlock language="python" filename="authenticated.py">{`from aquilia import Controller, Get
from aquilia.sessions import authenticated, SessionPrincipal


class ProfileController(Controller):
    prefix = "/profile"

    @Get("/")
    @authenticated
    async def me(self, ctx, principal: SessionPrincipal):
        """principal is auto-extracted from the session.
        Raises AuthenticationRequiredFault if not authenticated.
        """
        user = await User.objects.get(id=principal.id)
        return ctx.json({
            "id": user.id,
            "email": user.email,
            "kind": principal.kind,  # "user", "admin", etc.
            "attributes": principal.attributes,
        })

    @Get("/settings")
    @authenticated
    async def settings(self, ctx, principal: SessionPrincipal):
        prefs = await UserPrefs.objects.get(user_id=principal.id)
        return ctx.json(prefs.to_dict())`}</CodeBlock>
      </section>

      {/* @stateful */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>@stateful</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Wraps the session's data dictionary in a typed <code className="text-aquilia-500">SessionState</code> object, providing structured access with type-safe Field descriptors:
        </p>
        <CodeBlock language="python" filename="stateful.py">{`from aquilia import Controller, Get, Post
from aquilia.sessions import stateful
from aquilia.sessions.state import SessionState, Field


class CartState(SessionState):
    items: list = Field(default_factory=list)
    coupon_code: str = Field(default="")
    subtotal: float = Field(default=0.0)


class CartController(Controller):
    prefix = "/cart"

    @Get("/")
    @stateful(CartState)
    async def view_cart(self, ctx, state: CartState):
        """state is auto-synced from/to the session data dict."""
        return ctx.json({
            "items": state.items,
            "coupon": state.coupon_code,
            "subtotal": state.subtotal,
        })

    @Post("/add")
    @stateful(CartState)
    async def add_item(self, ctx, state: CartState):
        body = await ctx.json_body()
        state.items.append(body)
        state.subtotal += body.get("price", 0)
        # state changes auto-sync back to session.data on commit
        return ctx.json({"items": state.items})`}</CodeBlock>
      </section>

      {/* Decorator Comparison */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Decorator Comparison</h2>
        <div className={`overflow-x-auto ${boxClass}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
                <th className="text-left py-2 pr-4 font-semibold">Decorator</th>
                <th className="text-left py-2 pr-4 font-semibold">Creates?</th>
                <th className="text-left py-2 pr-4 font-semibold">Required?</th>
                <th className="text-left py-2 pr-4 font-semibold">Auth?</th>
                <th className="text-left py-2 font-semibold">On Failure</th>
              </tr>
            </thead>
            <tbody className={isDark ? 'text-gray-400' : 'text-gray-600'}>
              {[
                ['session.require()', '❌', '✅', '❌', 'SessionRequiredFault (401)'],
                ['session.require(authenticated=True)', '❌', '✅', '✅', 'AuthenticationRequiredFault (401)'],
                ['session.ensure()', '✅', '✅', '❌', 'Never fails'],
                ['session.optional()', '❌', '❌', '❌', 'session = None'],
                ['@authenticated', '❌', '✅', '✅', 'AuthenticationRequiredFault (401)'],
                ['@stateful(StateClass)', '✅', '✅', '❌', 'Never fails'],
              ].map(([dec, creates, required, auth, failure], i) => (
                <tr key={i} className={`border-b ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
                  <td className="py-2 pr-4"><code className="text-aquilia-500 text-xs">{dec}</code></td>
                  <td className="py-2 pr-4 text-xs">{creates}</td>
                  <td className="py-2 pr-4 text-xs">{required}</td>
                  <td className="py-2 pr-4 text-xs">{auth}</td>
                  <td className="py-2 text-xs">{failure}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Combining Decorators */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Combining with Other Decorators</h2>
        <CodeBlock language="python" filename="combined.py">{`from aquilia import Controller, Get, Post
from aquilia.sessions import session, authenticated
from aquilia.cache import cached
from aquilia.auth import guard


class OrderController(Controller):
    prefix = "/orders"

    @Get("/")
    @authenticated                          # Requires auth
    @cached(ttl=60)                         # Cache for 60s
    async def list_orders(self, ctx, principal):
        orders = await Order.objects.filter(user_id=principal.id)
        return ctx.json([o.to_dict() for o in orders])

    @Post("/")
    @session.require(authenticated=True)    # Requires auth session
    @guard("orders:create")                 # Permission check
    async def create_order(self, ctx, session):
        body = await ctx.json_body()
        order = await Order.create(
            user_id=session.principal.id,
            **body,
        )
        return ctx.json(order.to_dict(), status=201)`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
