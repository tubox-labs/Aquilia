import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Layers } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function SessionsState() {
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
          <Layers className="w-4 h-4" />
          Sessions / State
        </div>
        <h1 className={`text-4xl font-mono ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          <span className="font-bold tracking-tighter gradient-text relative group inline-block">
            Typed Session State
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-zinc-300' : 'text-zinc-700'}`}>
          The <DocTerm id="sessions.state">SessionState</DocTerm> system provides type-safe, structured access to session dictionaries. By defining typed states with <DocTerm id="sessions.field">Field</DocTerm> descriptors, you avoid raw string key access like <code className="text-aquilia-500">session["key"]</code>.
        </p>
      </div>

      {/* SessionState Base */}
      <section className="mb-16">
        <h2 className={sectionHeaderClass}>SessionState Base Class</h2>
        <p className={textClass}>
          Inheriting from <code className="text-aquilia-500">SessionState</code> enables typed field validation and default value seeding for session data dictionaries:
        </p>
        <CodeBlock language="python" filename="state_base.py" highlightLines={[8, 11, 14]}>{`from aquilia.sessions.state import SessionState, Field


class MyState(SessionState):
    """Define typed fields that sync with session.data."""
    
    # Field with a default value
    theme: str = Field(default="light")
    
    # Field with a factory (for mutable lists/dicts)
    cart_items: list = Field(default_factory=list)
    
    # Field with no default (returns None if missing from session data)
    user_name: str = Field()`}</CodeBlock>
      </section>

      {/* Field Descriptor - Clean Table */}
      <section className="mb-16">
        <h2 className={sectionHeaderClass}>Field Descriptor</h2>
        <p className={textClass}>
          The <DocTerm id="sessions.field">Field</DocTerm> class acts as a Python descriptor governing access and mutations. It takes two configuration parameters:
        </p>
        <div className="overflow-x-auto mb-6">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className={`border-b-2 ${isDark ? 'border-zinc-800 text-zinc-400' : 'border-zinc-200 text-zinc-500'} font-mono text-xs font-semibold`}>
                <th className="text-left py-3 pr-4">Parameter</th>
                <th className="text-left py-3 pr-4">Type</th>
                <th className="text-left py-3">Description</th>
              </tr>
            </thead>
            <tbody className={isDark ? 'text-zinc-300' : 'text-zinc-700'}>
              {[
                ['default', 'Any', 'The fallback value to return (and write to session.data) if the field key is missing.'],
                ['default_factory', 'Callable', 'A zero-argument callable returning mutable default values (like list or dict).'],
              ].map(([param, type, desc], i) => (
                <tr key={i} className={`border-b ${isDark ? 'border-zinc-900/50 hover:bg-white/[0.01]' : 'border-zinc-100 hover:bg-black/[0.01]'} transition-colors`}>
                  <td className="py-3 pr-4 font-mono text-xs"><code className="text-aquilia-500">{param}</code></td>
                  <td className="py-3 pr-4 text-xs"><code>{type}</code></td>
                  <td className="py-3 text-xs leading-relaxed">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* How Sync Works */}
      <section className="mb-16 border-t border-zinc-200 dark:border-zinc-800 pt-12">
        <h2 className={sectionHeaderClass}>How Synchronization Works</h2>
        <p className={textClass}>
          Typed states wrap the session data dictionary directly. Instantiating a state pulls/pushes keys to the underlying dictionary, updating dirty markers:
        </p>
        <CodeBlock language="python" filename="sync.py" highlightLines={[13, 16, 20, 24]}>{`from aquilia.sessions import Session, SessionID
from aquilia.sessions.state import SessionState, Field


class CartState(SessionState):
    items: list = Field(default_factory=list)
    coupon: str = Field(default="")


# 1. Create a session with existing data
session = Session(
    id=SessionID(),
    data={"items": [{"id": 1, "name": "Widget"}], "coupon": "SAVE20"},
)

# 2. Wrap the session data dictionary directly (no from_session classmethod exists)
state = CartState(session.data)

# 3. Read operations pull from session.data
print(state.items)   # [{"id": 1, "name": "Widget"}]
print(state.coupon)  # "SAVE20"

# 4. Write operations push to session.data and mark the session dirty
state.items.append({"id": 2, "name": "Gadget"})
state.coupon = "SAVE30"

print(session.data["items"])   # [{"id": 1, ...}, {"id": 2, ...}]
print(session.data["coupon"])  # "SAVE30"
print(session.is_dirty)        # True (marked dirty automatically!)`}</CodeBlock>
      </section>

      {/* Built-in State Examples */}
      <section className="mb-16 border-t border-zinc-200 dark:border-zinc-800 pt-12">
        <h2 className={sectionHeaderClass}>State Examples & Controller Binding</h2>

        <h3 className={`text-lg font-bold font-mono mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          CartState
        </h3>
        <p className={textClass}>
          Integrate typed states into controllers using the bare <DocTerm id="sessions.decorator_stateful">@stateful</DocTerm> decorator and a type-hinted <code className="text-aquilia-500">state</code> argument:
        </p>
        <CodeBlock language="python" filename="cart_state.py" highlightLines={[12, 13]}>{`from aquilia import Controller, Post
from aquilia.sessions import stateful
from aquilia.sessions.state import CartState


class CartController(Controller):
    prefix = "/cart"
    
    # Use bare @stateful decorator. Do NOT pass CartState as argument.
    # The decorator inspects type-hints of the 'state' parameter.
    @Post("/add")
    @stateful
    async def add(self, ctx, state: CartState):
        product = await ctx.request.json()
        state.items.append(product)
        state.subtotal += product.get("price", 0.0)
        return ctx.json({
            "items": len(state.items),
            "subtotal": state.subtotal,
            "currency": state.currency,
        })`}</CodeBlock>

        <h3 className={`text-lg font-bold font-mono mt-8 mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          UserPreferencesState
        </h3>
        <CodeBlock language="python" filename="prefs_state.py" highlightLines={[8, 14]}>{`from aquilia import Controller, Get, Post
from aquilia.sessions import stateful
from aquilia.sessions.state import UserPreferencesState


class SettingsController(Controller):
    prefix = "/settings"
    
    @Get("/")
    @stateful
    async def get_prefs(self, ctx, state: UserPreferencesState):
        return ctx.json({
            "theme": state.theme,
            "locale": state.language,
            "timezone": state.timezone,
        })
    
    @Post("/")
    @stateful
    async def update_prefs(self, ctx, state: UserPreferencesState):
        body = await ctx.request.json()
        if "theme" in body:
            state.theme = body["theme"]
        if "locale" in body:
            state.language = body["locale"]
        return ctx.json({"updated": True})`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
