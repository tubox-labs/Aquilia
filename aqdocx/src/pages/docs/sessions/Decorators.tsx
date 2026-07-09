import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Tag } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function SessionsDecorators() {
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
          <Tag className="w-4 h-4" />
          Sessions / Decorators
        </div>
        <h1 className={`text-4xl font-mono ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          <span className="font-bold tracking-tighter gradient-text relative group inline-block">
            Session Decorators
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-zinc-300' : 'text-zinc-700'}`}>
          Route decorators compile and inject session instances into controller endpoints.
          The <code className="text-aquilia-500">session</code> object exposes <code className="text-aquilia-500">.require()</code>, 
          <code className="text-aquilia-500">.ensure()</code>, and <code className="text-aquilia-500">.optional()</code> methods, 
          while <code className="text-aquilia-500">@stateful</code> binds typed states.
        </p>
      </div>

      {/* session.require() */}
      <section className="mb-16">
        <h2 className={sectionHeaderClass}>
          <DocTerm id="sessions.decorator_require">session.require()</DocTerm>
        </h2>
        <p className={textClass}>
          Enforces that a valid session exists. If no session is found, raises <code className="text-aquilia-500">SessionRequiredFault</code> (HTTP 401).
          If <code className="text-aquilia-500">authenticated=True</code> is passed, it additionally verifies authentication status, throwing an authentication fault if not logged in.
        </p>
        <CodeBlock language="python" filename="require.py" highlightLines={[8, 17, 24]}>{`from aquilia import Controller, Get
from aquilia.sessions import session, Session


class DashboardController(Controller):
    prefix = "/dashboard"

    @Get("/")
    @session.require()
    async def index(self, ctx, session: Session):
        """Only accessible with an existing session (anonymous or authenticated)."""
        return ctx.json({
            "user": session.principal.id if session.principal else None,
            "theme": session.get("theme", "light"),
        })

    @Get("/admin")
    @session.require(authenticated=True)
    async def admin(self, ctx, session: Session):
        """Requires session AND authenticated principal.
        Raises AUTH_REQUIRED fault if not authenticated.
        """
        return ctx.json({"admin": True, "user": session.principal.id})`}</CodeBlock>
      </section>

      {/* session.ensure() */}
      <section className="mb-16">
        <h2 className={sectionHeaderClass}>
          <DocTerm id="sessions.decorator_ensure">session.ensure()</DocTerm>
        </h2>
        <p className={textClass}>
          Ensures a session exists. If one is present in request headers/cookies, it is resolved; otherwise, a fresh anonymous session is initialized.
          This decorator is guaranteed never to fail.
        </p>
        <CodeBlock language="python" filename="ensure.py" highlightLines={[8, 14]}>{`from aquilia import Controller, Get, Post
from aquilia.sessions import session, Session


class CartController(Controller):
    prefix = "/cart"

    @Get("/")
    @session.ensure()
    async def view_cart(self, ctx, session: Session):
        """Always succeeds. Returns empty cart list if session is new."""
        return ctx.json({"items": session.get("cart", [])})

    @Post("/add")
    @session.ensure()
    async def add_to_cart(self, ctx, session: Session):
        """Reuses existing session, or creates a new one on the fly."""
        body = await ctx.request.json()
        cart = session.get("cart", [])
        cart.append(body)
        session["cart"] = cart # Triggers dirty state for save
        return ctx.json({"items": cart}, status=201)`}</CodeBlock>
      </section>

      {/* session.optional() */}
      <section className="mb-16">
        <h2 className={sectionHeaderClass}>
          <DocTerm id="sessions.decorator_optional">session.optional()</DocTerm>
        </h2>
        <p className={textClass}>
          Resolves a session if present, but does not construct a new session on failure. The session argument is injected as <code className="text-aquilia-500">None</code> if missing.
        </p>
        <CodeBlock language="python" filename="optional.py" highlightLines={[9, 10]}>{`from aquilia import Controller, Get
from aquilia.sessions import session, Session


class ProductController(Controller):
    prefix = "/products"

    @Get("/:id")
    @session.optional()
    async def show(self, ctx, id: str, session: Session | None):
        """Session may be None."""
        product = await Product.objects.get(id=id)
        
        theme = "light"
        if session:
            theme = session.get("theme", "light")
            # Track recently viewed list
            viewed = session.get("recently_viewed", [])
            viewed.append(id)
            session["recently_viewed"] = viewed[-5:]
        
        return ctx.json({"product": product.to_dict(), "theme": theme})`}</CodeBlock>
      </section>

      {/* @stateful */}
      <section className="mb-16">
        <h2 className={sectionHeaderClass}>
          <DocTerm id="sessions.decorator_stateful">@stateful</DocTerm>
        </h2>
        <p className={textClass}>
          A bare decorator that inspects type hints of the parameter named <code className="text-aquilia-500">state</code>.
          It instantiates that typed state class wrapping the session's data dictionary, automatically syncing modifications.
        </p>
        <CodeBlock language="python" filename="stateful.py" highlightLines={[12, 17]}>{`from aquilia import Controller, Get, Post
from aquilia.sessions import stateful
from aquilia.sessions.state import SessionState, Field

class CartState(SessionState):
    items: list = Field(default_factory=list)
    subtotal: float = Field(default=0.0)

class CartController(Controller):
    prefix = "/cart"

    @Get("/")
    @stateful
    async def view_cart(self, ctx, state: CartState):
        """CartState is auto-resolved using type hints of 'state'."""
        return ctx.json({"items": state.items, "subtotal": state.subtotal})

    @Post("/add")
    @stateful
    async def add_item(self, ctx, state: CartState):
        body = await ctx.request.json()
        state.items.append(body)
        state.subtotal += body.get("price", 0.0)
        # Auto-committed to session on handler completion
        return ctx.json({"items": state.items})`}</CodeBlock>
      </section>

      {/* Decorator Comparison - Clean Table */}
      <section className="mb-16 border-t border-zinc-200 dark:border-zinc-800 pt-12">
        <h2 className={sectionHeaderClass}>Decorator Comparison</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className={`border-b-2 ${isDark ? 'border-zinc-800 text-zinc-400' : 'border-zinc-200 text-zinc-500'} font-mono text-xs font-semibold`}>
                <th className="text-left py-3 pr-4">Decorator</th>
                <th className="text-left py-3 pr-4">Creates Session?</th>
                <th className="text-left py-3 pr-4">Required?</th>
                <th className="text-left py-3 pr-4">Auth Required?</th>
                <th className="text-left py-3">On Failure</th>
              </tr>
            </thead>
            <tbody className={isDark ? 'text-zinc-300' : 'text-zinc-700'}>
              {[
                ['session.require()', '❌ No', '✅ Yes', '❌ No', 'SessionRequiredFault (HTTP 401)'],
                ['session.require(authenticated=True)', '❌ No', '✅ Yes', '✅ Yes', 'AUTH_REQUIRED fault (HTTP 401)'],
                ['session.ensure()', '✅ Yes', '✅ Yes', '❌ No', 'Never fails'],
                ['session.optional()', '❌ No', '❌ No', '❌ No', 'Injects None'],
                ['@stateful', '✅ Yes', '✅ Yes', '❌ No', 'Never fails'],
              ].map(([dec, creates, required, auth, failure], i) => (
                <tr key={i} className={`border-b ${isDark ? 'border-zinc-900/50 hover:bg-white/[0.01]' : 'border-zinc-100 hover:bg-black/[0.01]'} transition-colors`}>
                  <td className="py-3 pr-4 font-mono text-xs"><code className="text-aquilia-500">{dec}</code></td>
                  <td className="py-3 pr-4 text-xs font-medium">{creates}</td>
                  <td className="py-3 pr-4 text-xs">{required}</td>
                  <td className="py-3 pr-4 text-xs">{auth}</td>
                  <td className="py-3 text-xs leading-relaxed">{failure}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Combining Decorators */}
      <section className="mb-16 border-t border-zinc-200 dark:border-zinc-800 pt-12">
        <h2 className={sectionHeaderClass}>Combining with Auth System</h2>
        <p className={textClass}>
          Combine session decorators with auth helpers like `@authenticated` from the authentication module or permission-checking guards:
        </p>
        <CodeBlock language="python" filename="combined.py" highlightLines={[1, 10, 11, 17, 18]}>{`from aquilia.auth import authenticated, guard
from aquilia.sessions import session


class OrderController(Controller):
    prefix = "/orders"

    @Get("/")
    @authenticated                          # Enforces authentication (auth module)
    @guard("orders:read")                   # Enforces permission (auth module)
    async def list_orders(self, ctx, principal):
        orders = await Order.objects.filter(user_id=principal.id)
        return ctx.json([o.to_dict() for o in orders])

    @Post("/")
    @session.require(authenticated=True)    # Enforces session & auth
    @guard("orders:create")                 # Enforces permission check
    async def create_order(self, ctx, session):
        body = await ctx.request.json()
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
