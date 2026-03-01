import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Layers } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function SessionsState() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Layers className="w-4 h-4" />
          Sessions / State
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Typed Session State
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">SessionState</code> system provides typed, structured access to session data using <code className="text-aquilia-500">Field</code> descriptors. Instead of accessing <code className="text-aquilia-500">session["key"]</code> with string keys, you define a state class with typed fields that auto-sync from/to the session's data dictionary.
        </p>
      </div>

      {/* SessionState Base */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>SessionState Base Class</h2>
        <CodeBlock language="python" filename="state_base.py">{`from aquilia.sessions.state import SessionState, Field


class MyState(SessionState):
    """Define typed fields that sync with session.data."""
    
    # Field with a default value
    theme: str = Field(default="light")
    
    # Field with a factory (for mutable defaults)
    cart_items: list = Field(default_factory=list)
    
    # Field with no default (must exist in session data)
    user_name: str = Field()
    
    # Numeric field with default
    page_views: int = Field(default=0)`}</CodeBlock>
      </section>

      {/* Field Descriptor */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Field Descriptor</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <code className="text-aquilia-500">Field</code> is a Python descriptor that manages the bidirectional sync between the state object and the underlying session data dict:
        </p>
        <div className={`overflow-x-auto ${boxClass}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
                <th className="text-left py-2 pr-4 font-semibold">Parameter</th>
                <th className="text-left py-2 pr-4 font-semibold">Type</th>
                <th className="text-left py-2 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className={isDark ? 'text-gray-400' : 'text-gray-600'}>
              {[
                ['default', 'Any', 'Default value if key is missing from session data'],
                ['default_factory', 'Callable', 'Factory function for mutable defaults (list, dict)'],
                ['key', 'str | None', 'Override the session data key (defaults to field name)'],
              ].map(([param, type, desc], i) => (
                <tr key={i} className={`border-b ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
                  <td className="py-2 pr-4"><code className="text-aquilia-500 text-xs">{param}</code></td>
                  <td className="py-2 pr-4 text-xs"><code>{type}</code></td>
                  <td className="py-2 text-xs">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <CodeBlock language="python" filename="field_details.py">{`class PreferencesState(SessionState):
    # Use a custom key in the session data dict
    dark_mode: bool = Field(default=False, key="prefs_dark_mode")
    
    # session.data["prefs_dark_mode"] ↔ state.dark_mode
    
    # Factory for mutable defaults — called per state instance
    tags: list = Field(default_factory=list)
    
    # Without default — AttributeError if missing
    user_id: str = Field()`}</CodeBlock>
      </section>

      {/* How Sync Works */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>How Sync Works</h2>
        <CodeBlock language="python" filename="sync.py">{`from aquilia.sessions import Session, SessionID
from aquilia.sessions.state import SessionState, Field


class CartState(SessionState):
    items: list = Field(default_factory=list)
    coupon: str = Field(default="")


# 1. Create a session with existing data
session = Session(
    id=SessionID.generate(),
    data={"items": [{"id": 1, "name": "Widget"}], "coupon": "SAVE20"},
)

# 2. Wrap session data in typed state
state = CartState.from_session(session)

# 3. Read — pulls from session.data
print(state.items)   # [{"id": 1, "name": "Widget"}]
print(state.coupon)  # "SAVE20"

# 4. Write — pushes to session.data
state.items.append({"id": 2, "name": "Gadget"})
state.coupon = "SAVE30"

# 5. Verify sync
print(session.data["items"])   # [{"id": 1, ...}, {"id": 2, ...}]
print(session.data["coupon"])  # "SAVE30"
print(session._dirty)          # True — changes tracked!`}</CodeBlock>
      </section>

      {/* Built-in State Examples */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Built-in State Examples</h2>

        <h3 className={`text-xl font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>CartState</h3>
        <CodeBlock language="python" filename="cart_state.py">{`from aquilia.sessions.state import CartState

# CartState provides structured cart management:
class CartState(SessionState):
    items: list = Field(default_factory=list)
    coupon_code: str = Field(default="")
    subtotal: float = Field(default=0.0)
    currency: str = Field(default="USD")


# Usage with @stateful:
from aquilia.sessions import stateful

class CartController(Controller):
    prefix = "/cart"
    
    @Post("/add")
    @stateful(CartState)
    async def add(self, ctx, state: CartState):
        product = await ctx.json_body()
        state.items.append(product)
        state.subtotal += product["price"]
        return ctx.json({
            "items": len(state.items),
            "subtotal": state.subtotal,
            "currency": state.currency,
        })`}</CodeBlock>

        <h3 className={`text-xl font-semibold mt-8 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>UserPreferencesState</h3>
        <CodeBlock language="python" filename="prefs_state.py">{`from aquilia.sessions.state import UserPreferencesState

# UserPreferencesState provides common user preferences:
class UserPreferencesState(SessionState):
    theme: str = Field(default="light")
    locale: str = Field(default="en-US")
    timezone: str = Field(default="UTC")
    notifications_enabled: bool = Field(default=True)
    items_per_page: int = Field(default=25)


# Usage:
class SettingsController(Controller):
    prefix = "/settings"
    
    @Get("/")
    @stateful(UserPreferencesState)
    async def get_prefs(self, ctx, state: UserPreferencesState):
        return ctx.json({
            "theme": state.theme,
            "locale": state.locale,
            "timezone": state.timezone,
            "notifications": state.notifications_enabled,
            "per_page": state.items_per_page,
        })
    
    @Post("/")
    @stateful(UserPreferencesState)
    async def update_prefs(self, ctx, state: UserPreferencesState):
        body = await ctx.json_body()
        if "theme" in body:
            state.theme = body["theme"]
        if "locale" in body:
            state.locale = body["locale"]
        if "timezone" in body:
            state.timezone = body["timezone"]
        return ctx.json({"updated": True})`}</CodeBlock>
      </section>

      {/* Custom State Classes */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Custom State Classes</h2>
        <CodeBlock language="python" filename="custom_state.py">{`from aquilia.sessions.state import SessionState, Field


class WizardState(SessionState):
    """Multi-step form wizard state."""
    current_step: int = Field(default=1)
    total_steps: int = Field(default=5)
    form_data: dict = Field(default_factory=dict)
    completed_steps: list = Field(default_factory=list)
    
    def advance(self):
        if self.current_step not in self.completed_steps:
            self.completed_steps.append(self.current_step)
        self.current_step = min(self.current_step + 1, self.total_steps)
    
    def go_back(self):
        self.current_step = max(self.current_step - 1, 1)
    
    @property
    def progress(self) -> float:
        return len(self.completed_steps) / self.total_steps


class OnboardingController(Controller):
    prefix = "/onboarding"

    @Get("/step/:n")
    @stateful(WizardState)
    async def get_step(self, ctx, n: int, state: WizardState):
        return ctx.json({
            "current_step": state.current_step,
            "form_data": state.form_data,
            "progress": state.progress,
        })

    @Post("/step/:n")
    @stateful(WizardState)
    async def submit_step(self, ctx, n: int, state: WizardState):
        body = await ctx.json_body()
        state.form_data[str(n)] = body
        state.advance()
        return ctx.json({
            "next_step": state.current_step,
            "progress": state.progress,
        })`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
