import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Eye } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function BlueprintsProjections() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Eye className="w-4 h-4" />
          Blueprints / Projections
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Projections
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Projections let you define named subsets of fields within a single Blueprint. Instead of creating separate Blueprints for list views vs detail views vs admin views, you declare projections and select them at render time.
        </p>
      </div>

      {/* Why Projections */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Why Projections?</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {[
            { title: 'One Blueprint, Many Views', desc: 'A single ProductBlueprint serves list, detail, admin, and public views' },
            { title: 'No Duplication', desc: 'Validation rules, Facet configs, and seal methods are defined once' },
            { title: 'Security', desc: 'Sensitive fields can be excluded from specific projections' },
            { title: 'Performance', desc: 'Minimal projections skip expensive computed/lens fields' },
          ].map((item, i) => (
            <div key={i} className={boxClass}>
              <h3 className={`font-bold text-sm mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>{item.title}</h3>
              <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Defining Projections */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Defining Projections</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Projections are declared in the <code className="text-aquilia-500">Spec</code> inner class as a dictionary mapping names to field lists.
        </p>
        <CodeBlock language="python" filename="projections.py">{`from aquilia.blueprints import Blueprint, TextFacet, EmailFacet, FloatFacet, Computed, Lens


class ProductBlueprint(Blueprint):
    name = TextFacet(max_length=200)
    slug = TextFacet(max_length=100)
    price = FloatFacet()
    description = TextFacet(max_length=5000)
    internal_notes = TextFacet(max_length=2000)
    category = TextFacet()
    sku = TextFacet()
    stock_count = IntFacet()
    is_active = BoolFacet()
    created_at = DateTimeFacet(read_only=True)
    reviews = Lens("ReviewBlueprint", many=True)
    
    # Computed field
    display_price = Computed(lambda inst: "$%.2f" % inst.price)

    class Spec:
        model = Product
        fields = "__all__"
        read_only_fields = ["id", "created_at"]
        
        # Projection definitions
        projections = {
            # Minimal fields for list/search views
            "__minimal__": ["id", "name", "price", "slug"],
            
            # Summary for card displays
            "summary": ["id", "name", "price", "category", "display_price", "is_active"],
            
            # Full detail view (excludes internal data)
            "detail": ["-internal_notes", "-stock_count"],
            
            # Admin view — everything
            "__all__": "__all__",
            
            # Public view — explicitly listed fields
            "public": ["id", "name", "price", "description", "category", "reviews"],
        }
        
        # Default projection when none specified
        default_projection = "summary"`}</CodeBlock>
      </section>

      {/* Special Projection Names */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Special Projection Names</h2>
        <div className={`overflow-hidden rounded-xl border ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={isDark ? 'bg-zinc-900' : 'bg-gray-50'}>
                <th className={`text-left py-3 px-4 font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Name</th>
                <th className={`text-left py-3 px-4 font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Meaning</th>
              </tr>
            </thead>
            <tbody className={isDark ? 'divide-y divide-white/5' : 'divide-y divide-gray-100'}>
              {[
                { name: '"__all__"', desc: 'Include all declared fields — no filtering applied' },
                { name: '"__minimal__"', desc: 'Convention for the smallest useful subset (ID + key identifiers)' },
                { name: '["-field"]', desc: 'Exclusion syntax — include all fields EXCEPT the prefixed ones' },
                { name: '["field1", "field2"]', desc: 'Explicit inclusion — only these fields' },
              ].map((row, i) => (
                <tr key={i} className={isDark ? 'bg-[#0A0A0A]' : 'bg-white'}>
                  <td className="py-2 px-4"><code className="text-aquilia-500 font-mono text-xs">{row.name}</code></td>
                  <td className={`py-2 px-4 text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{row.desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Using Projections */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Using Projections</h2>
        <CodeBlock language="python" filename="usage.py">{`product = await Product.objects.get(id=1)

# Use default projection ("summary")
data = ProductBlueprint(instance=product).data
# {"id": 1, "name": "Widget", "price": 9.99, "category": "electronics", ...}

# Use minimal projection
data = ProductBlueprint(instance=product, projection="__minimal__").data
# {"id": 1, "name": "Widget", "price": 9.99, "slug": "widget"}

# Use detail projection (excludes internal_notes, stock_count)
data = ProductBlueprint(instance=product, projection="detail").data

# Use admin projection (all fields)
data = ProductBlueprint(instance=product, projection="__all__").data

# Serialize many instances with projection
products = await Product.objects.all()
data = ProductBlueprint(instance=products, many=True, projection="__minimal__").data`}</CodeBlock>
      </section>

      {/* Projections with Controllers */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Projections in Controllers</h2>
        <CodeBlock language="python" filename="controller.py">{`from aquilia import Controller, Get


class ProductController(Controller):
    prefix = "/api/products"

    @Get("/")
    async def list_products(self, ctx):
        products = await Product.objects.all()
        # Minimal projection for list views — fast, small payload
        return ctx.json(
            ProductBlueprint(instance=products, many=True, projection="__minimal__").data
        )

    @Get("/{id:int}")
    async def detail(self, ctx, id: int):
        product = await Product.objects.get(id=id)
        # Full detail projection
        return ctx.json(
            ProductBlueprint(instance=product, projection="detail").data
        )

    @Get("/{id:int}/admin")
    async def admin_detail(self, ctx, id: int):
        product = await Product.objects.get(id=id)
        # Admin sees everything
        return ctx.json(
            ProductBlueprint(instance=product, projection="__all__").data
        )`}</CodeBlock>
      </section>

      {/* Subscript Syntax */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Subscript Syntax for Lenses</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          When using <code className="text-aquilia-500">Lens</code> facets, you can select which projection the nested Blueprint uses via Python's subscript syntax:
        </p>
        <CodeBlock language="python" filename="subscript.py">{`from aquilia.blueprints import Blueprint, Lens

class OrderBlueprint(Blueprint):
    # Render products with their "summary" projection
    items = Lens(ProductBlueprint["summary"], many=True)
    
    # Render customer with "public" projection
    customer = Lens(CustomerBlueprint["public"])

    class Spec:
        model = Order
        fields = "__all__"

# This is shorthand for:
# items = Lens(ProductBlueprint, many=True, projection="summary")`}</CodeBlock>
      </section>

      {/* ProjectionRegistry API */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>ProjectionRegistry API</h2>
        <CodeBlock language="python" filename="registry.py">{`# Inspect available projections
print(ProductBlueprint._projections.available)
# ["__minimal__", "summary", "detail", "__all__", "public"]

# Get default projection name
print(ProductBlueprint._projections.default_name)
# "summary"

# Resolve a projection to field names
fields = ProductBlueprint._projections.resolve("__minimal__")
# ["id", "name", "price", "slug"]

# Resolve exclusion projection
fields = ProductBlueprint._projections.resolve("detail")
# All fields except "internal_notes" and "stock_count"`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
