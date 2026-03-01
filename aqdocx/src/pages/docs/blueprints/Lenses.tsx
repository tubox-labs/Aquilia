import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { GitBranch } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function BlueprintsLenses() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <GitBranch className="w-4 h-4" />
          Blueprints / Lenses
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Lenses
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Lenses are a special Facet type that renders related objects through another Blueprint. They provide depth-controlled, cycle-safe relational views — eliminating the need for manual nested serialization or N+1 query problems in your API responses.
        </p>
      </div>

      {/* Core Concept */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Core Concept</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          A Lens is a Facet that delegates serialization to another Blueprint. When the parent Blueprint renders, each Lens field creates an instance of the target Blueprint and renders the related object through it.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[
            { title: 'Depth Control', desc: 'Maximum nesting depth prevents infinite recursion (default: 3 levels)' },
            { title: 'Cycle Detection', desc: 'Automatically detects and prevents circular Blueprint references' },
            { title: 'Projection Selection', desc: 'Choose which projection the nested Blueprint uses' },
          ].map((item, i) => (
            <div key={i} className={boxClass}>
              <h3 className={`font-bold text-sm mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>{item.title}</h3>
              <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Basic Usage */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Basic Usage</h2>
        <CodeBlock language="python" filename="lenses.py">{`from aquilia.blueprints import Blueprint, TextFacet, IntFacet, Lens


class CategoryBlueprint(Blueprint):
    name = TextFacet(max_length=100)
    slug = TextFacet(max_length=100)

    class Spec:
        model = Category
        fields = ["id", "name", "slug"]


class ReviewBlueprint(Blueprint):
    rating = IntFacet(min_value=1, max_value=5)
    comment = TextFacet(max_length=500)
    author = TextFacet(source="author.username", read_only=True)

    class Spec:
        model = Review
        fields = ["id", "rating", "comment", "author"]


class ProductBlueprint(Blueprint):
    name = TextFacet(max_length=200)
    price = FloatFacet()

    # Single related object (ForeignKey)
    category = Lens(CategoryBlueprint)

    # Multiple related objects (reverse FK / M2M)
    reviews = Lens(ReviewBlueprint, many=True)

    class Spec:
        model = Product
        fields = "__all__"


# Output:
# {
#   "id": 1,
#   "name": "Widget",
#   "price": 9.99,
#   "category": {
#     "id": 5,
#     "name": "Electronics",
#     "slug": "electronics"
#   },
#   "reviews": [
#     {"id": 10, "rating": 5, "comment": "Great!", "author": "alice"},
#     {"id": 11, "rating": 4, "comment": "Good", "author": "bob"},
#   ]
# }`}</CodeBlock>
      </section>

      {/* Depth Control */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Depth Control</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Lenses track nesting depth. When maximum depth is reached, the Lens falls back to rendering the primary key instead of the full nested object.
        </p>
        <CodeBlock language="python" filename="depth.py">{`# Default max_depth is 3
category = Lens(CategoryBlueprint, max_depth=2)

# At depth 0: Full nested object   {"id": 5, "name": "Electronics", "slug": "..."}
# At depth 1: Full nested object   (still within limit)
# At depth 2: Primary key only     5  (max_depth reached)

# Custom depth for deep hierarchies
comments = Lens(CommentBlueprint, many=True, max_depth=5)


# Example: Category with subcategories
class CategoryBlueprint(Blueprint):
    name = TextFacet()
    
    # Self-referential lens with depth control
    subcategories = Lens("CategoryBlueprint", many=True, max_depth=3)
    parent = Lens("CategoryBlueprint", max_depth=1)

    class Spec:
        model = Category
        fields = ["id", "name", "subcategories", "parent"]

# Depth 0: {"id": 1, "name": "Root", "subcategories": [
#   {"id": 2, "name": "Child", "subcategories": [
#     {"id": 3, "name": "Grandchild", "subcategories": [4, 5]}  ← PKs at max depth
#   ]}
# ]}`}</CodeBlock>
      </section>

      {/* Cycle Detection */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Cycle Detection</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          If Blueprint A references Blueprint B which references Blueprint A, Aquilia detects this cycle and raises <code className="text-aquilia-500">LensCycleFault</code> instead of producing infinite recursion.
        </p>
        <CodeBlock language="python" filename="cycle.py">{`class AuthorBlueprint(Blueprint):
    name = TextFacet()
    books = Lens("BookBlueprint", many=True)  # Forward reference

    class Spec:
        model = Author
        fields = ["id", "name", "books"]


class BookBlueprint(Blueprint):
    title = TextFacet()
    author = Lens(AuthorBlueprint)  # Circular reference!

    class Spec:
        model = Book
        fields = ["id", "title", "author"]


# Rendering:
# AuthorBlueprint renders → books → BookBlueprint → author → AuthorBlueprint
# At this point, cycle is detected and rendering stops with PK fallback.
# No LensCycleFault unless max_depth is also exceeded.

# If you want to catch cycles explicitly:
from aquilia.blueprints.exceptions import LensCycleFault

try:
    data = AuthorBlueprint(instance=author).data
except LensCycleFault as e:
    print(e.blueprint_chain)  # ["AuthorBlueprint", "BookBlueprint", "AuthorBlueprint"]`}</CodeBlock>
      </section>

      {/* Projection Selection */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Projection Selection with Subscript Syntax</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Use Python's subscript syntax <code className="text-aquilia-500">Blueprint["projection"]</code> to control which projection the nested Blueprint uses:
        </p>
        <CodeBlock language="python" filename="projection_lens.py">{`class OrderBlueprint(Blueprint):
    # Products rendered with minimal fields (fast list)
    items = Lens(ProductBlueprint["__minimal__"], many=True)
    
    # Customer rendered with public-safe fields
    customer = Lens(CustomerBlueprint["public"])
    
    # Shipping address with full detail
    address = Lens(AddressBlueprint["detail"])

    class Spec:
        model = Order
        fields = "__all__"

# Output:
# {
#   "id": 100,
#   "items": [
#     {"id": 1, "name": "Widget", "price": 9.99, "slug": "widget"},  ← minimal
#     {"id": 2, "name": "Gadget", "price": 19.99, "slug": "gadget"}, ← minimal
#   ],
#   "customer": {"id": 42, "name": "Alice"},                         ← public
#   "address": {"street": "123 Main St", "city": "NYC", "zip": "..."}  ← detail
# }`}</CodeBlock>
      </section>

      {/* Forward References */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Forward References (Lazy Resolution)</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          When Blueprint classes reference each other, use string names for forward references. They resolve lazily from the global Blueprint registry:
        </p>
        <CodeBlock language="python" filename="forward_ref.py">{`class AuthorBlueprint(Blueprint):
    name = TextFacet()
    
    # Forward reference — BookBlueprint hasn't been defined yet
    books = Lens("BookBlueprint", many=True)

    class Spec:
        model = Author
        fields = ["id", "name", "books"]


# BookBlueprint defined later
class BookBlueprint(Blueprint):
    title = TextFacet()
    author = Lens(AuthorBlueprint)  # Direct reference (already defined)

    class Spec:
        model = Book
        fields = ["id", "title", "author"]


# Both work:
# Lens(AuthorBlueprint)        — Direct class reference
# Lens("AuthorBlueprint")      — String forward reference
# Lens("BookBlueprint")        — Resolved from _blueprint_registry`}</CodeBlock>
      </section>

      {/* Lens with Inbound Data */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Lens Behavior on Input</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          On inbound (input) data, Lenses accept the primary key value rather than nested objects. This prevents clients from arbitrarily modifying related objects through the parent:
        </p>
        <CodeBlock language="python" filename="inbound.py">{`# Input payload for creating an order:
{
    "customer_id": 42,         # FK via IntFacet (not nested object)
    "items": [1, 2, 3],        # M2M via ListFacet(IntFacet)
    "shipping_address": {      # Nested create uses NestedBlueprintFacet
        "street": "123 Main",
        "city": "NYC"
    }
}

# If you want nested write support, use NestedBlueprintFacet 
# from aquilia.blueprints.annotations instead of Lens`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
