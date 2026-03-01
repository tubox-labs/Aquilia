import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Plug } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function BlueprintsIntegration() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Plug className="w-4 h-4" />
          Blueprints / Controller Integration
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Controller Integration
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Blueprints integrate deeply with Aquilia's Controllers, DI Container, Auth system, and Sessions. This page shows how Blueprints work as part of the full request lifecycle.
        </p>
      </div>

      {/* Auto-Binding */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Auto-Binding to Request</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          When a controller handler declares a Blueprint type hint, Aquilia automatically parses the request body and creates a Blueprint instance via <code className="text-aquilia-500">bind_blueprint_to_request()</code>:
        </p>
        <CodeBlock language="python" filename="auto_binding.py">{`from aquilia import Controller, Post, Put, Get
from myapp.blueprints import ProductBlueprint


class ProductController(Controller):
    prefix = "/api/products"

    @Post("/", status_code=201)
    async def create(self, ctx, payload: ProductBlueprint):
        """
        'payload' is automatically:
        1. Parsed from request JSON/form body
        2. Instantiated as ProductBlueprint(data=body)
        3. Context injected with request + DI container
        """
        if not payload.is_sealed():
            return ctx.json(payload.errors, status=422)

        product = payload.imprint()
        await product.save()
        return ctx.json(ProductBlueprint(instance=product).data, status=201)

    @Put("/{id:int}")
    async def update(self, ctx, id: int, payload: ProductBlueprint):
        product = await Product.objects.get(id=id)

        if not payload.is_sealed():
            return ctx.json(payload.errors, status=422)

        payload.imprint(instance=product, partial=True)
        await product.save()
        return ctx.json(ProductBlueprint(instance=product).data)`}</CodeBlock>
      </section>

      {/* With Projections */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Response Rendering with Projections</h2>
        <CodeBlock language="python" filename="render_response.py">{`from aquilia import Controller, Get
from myapp.blueprints import ProductBlueprint


class ProductController(Controller):
    prefix = "/api/products"

    @Get("/")
    async def list_products(self, ctx):
        products = await Product.objects.all()
        
        # Minimal projection for list views
        bp = ProductBlueprint(
            instance=products,
            many=True,
            projection="__minimal__"
        )
        return ctx.json(bp.data)

    @Get("/{id:int}")
    async def detail(self, ctx, id: int):
        product = await Product.objects.get(id=id)
        
        # Full detail projection
        bp = ProductBlueprint(instance=product, projection="detail")
        return ctx.json(bp.data)

    @Get("/{id:int}/admin")
    async def admin_view(self, ctx, id: int):
        product = await Product.objects.get(id=id)
        
        # Admin projection with all fields
        bp = ProductBlueprint(instance=product, projection="__all__")
        return ctx.json(bp.data)`}</CodeBlock>
      </section>

      {/* DI Integration */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>DI Container Integration</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Blueprints can resolve dependencies from the DI container using the <code className="text-aquilia-500">Inject</code> facet:
        </p>
        <CodeBlock language="python" filename="di_integration.py">{`from aquilia.blueprints import Blueprint, TextFacet, Inject, Hidden
from aquilia.di import Singleton


# Register a service in DI
class PricingService:
    def calculate_tax(self, price: float, region: str) -> float:
        rates = {"US": 0.08, "EU": 0.20, "UK": 0.20}
        return price * rates.get(region, 0.10)

# In workspace.py: container.singleton(PricingService)


class InvoiceBlueprint(Blueprint):
    amount = FloatFacet()
    region = TextFacet(max_length=10)
    
    # Inject service from DI container
    pricing = Inject(token=PricingService)
    
    # Hidden — populated by context, never exposed in I/O
    created_by_id = Hidden()

    class Spec:
        model = Invoice
        fields = ["amount", "region"]

    def seal_tax_calculation(self, data):
        """Use injected service for validation."""
        tax = self.pricing.calculate_tax(data["amount"], data["region"])
        if tax > 1000:
            self.reject("amount", "Invoice amount exceeds tax threshold.")`}</CodeBlock>
      </section>

      {/* Auth Integration */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Auth Integration</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Combine Blueprints with Aquilia's auth guards for secure endpoints:
        </p>
        <CodeBlock language="python" filename="auth_integration.py">{`from aquilia import Controller, Post, Get
from aquilia.auth import guard, AuthGuard
from myapp.blueprints import ArticleBlueprint


class ArticleController(Controller):
    prefix = "/api/articles"

    @Post("/", status_code=201)
    @guard(AuthGuard)  # Require authentication
    async def create(self, ctx, payload: ArticleBlueprint):
        """Create article — requires authenticated user."""
        if not payload.is_sealed():
            return ctx.json(payload.errors, status=422)

        # Inject the authenticated user as the author
        article = payload.imprint()
        article.author = ctx.user  # From auth guard
        await article.save()

        return ctx.json(ArticleBlueprint(instance=article).data, status=201)

    @Get("/")
    async def list_articles(self, ctx):
        """Public endpoint — no auth required."""
        articles = await Article.objects.filter(published=True)
        return ctx.json(
            ArticleBlueprint(
                instance=articles,
                many=True,
                projection="public"
            ).data
        )


# Blueprint with auth-aware validation:
class AdminSettingsBlueprint(Blueprint):
    maintenance_mode = BoolFacet(default=False)
    max_upload_size = IntFacet(min_value=1, max_value=100)

    class Spec:
        model = Settings
        fields = ["maintenance_mode", "max_upload_size"]

    async def async_seal_admin_only(self, data):
        """Only admins can change maintenance mode."""
        if data.get("maintenance_mode") and not self.context.get("is_admin"):
            self.reject("maintenance_mode", "Only admins can enable maintenance mode.")`}</CodeBlock>
      </section>

      {/* Sessions Integration */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Sessions Integration</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Blueprints can access session data for validation and conditional logic:
        </p>
        <CodeBlock language="python" filename="sessions_integration.py">{`from aquilia import Controller, Post
from aquilia.sessions import session, authenticated
from myapp.blueprints import CartBlueprint


class CartController(Controller):
    prefix = "/api/cart"

    @Post("/checkout")
    @authenticated  # Require authenticated session
    async def checkout(self, ctx):
        """Checkout flow using session data + Blueprint."""
        # Get cart items from session
        cart_items = ctx.session.get("cart", [])
        
        # Validate checkout data with Blueprint
        bp = CheckoutBlueprint(data={
            "items": cart_items,
            "shipping_address": await ctx.json(),
        })

        if not bp.is_sealed():
            return ctx.json(bp.errors, status=422)

        order = bp.imprint()
        order.user = ctx.session.principal
        await order.save()

        # Clear cart from session
        ctx.session.delete("cart")

        return ctx.json(OrderBlueprint(instance=order).data, status=201)


class CheckoutBlueprint(Blueprint):
    items = ListFacet(child=IntFacet(), min_items=1)
    shipping_address = NestedBlueprintFacet(AddressBlueprint)

    class Spec:
        model = Order
        fields = ["items", "shipping_address"]

    def seal_cart_not_empty(self, data):
        if not data.get("items"):
            self.reject("items", "Your cart is empty.")`}</CodeBlock>
      </section>

      {/* Full CRUD Example */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Full CRUD Example</h2>
        <CodeBlock language="python" filename="full_crud.py">{`from aquilia import Controller, Get, Post, Put, Patch, Delete
from aquilia.auth import guard, AuthGuard
from myapp.blueprints import ProductBlueprint


class ProductController(Controller):
    prefix = "/api/products"

    @Get("/")
    async def list(self, ctx):
        products = await Product.objects.all()
        return ctx.json(
            ProductBlueprint(instance=products, many=True, projection="__minimal__").data
        )

    @Get("/{id:int}")
    async def retrieve(self, ctx, id: int):
        product = await Product.objects.get(id=id)
        return ctx.json(ProductBlueprint(instance=product, projection="detail").data)

    @Post("/", status_code=201)
    @guard(AuthGuard)
    async def create(self, ctx, payload: ProductBlueprint):
        if not await payload.is_sealed_async():
            return ctx.json(payload.errors, status=422)
        product = payload.imprint()
        await product.save()
        return ctx.json(ProductBlueprint(instance=product).data, status=201)

    @Patch("/{id:int}")
    @guard(AuthGuard)
    async def partial_update(self, ctx, id: int, payload: ProductBlueprint):
        product = await Product.objects.get(id=id)
        # partial=True: only validate provided fields
        bp = ProductBlueprint(data=await ctx.json(), partial=True)
        if not bp.is_sealed():
            return ctx.json(bp.errors, status=422)
        bp.imprint(instance=product, partial=True)
        await product.save()
        return ctx.json(ProductBlueprint(instance=product).data)

    @Delete("/{id:int}", status_code=204)
    @guard(AuthGuard)
    async def destroy(self, ctx, id: int):
        product = await Product.objects.get(id=id)
        await product.delete()
        return ctx.empty()`}</CodeBlock>
      </section>

      {/* render_blueprint_response */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Utility Functions</h2>
        <CodeBlock language="python" filename="utilities.py">{`from aquilia.blueprints.integration import (
    bind_blueprint_to_request,
    render_blueprint_response,
    resolve_blueprint_from_annotation,
    is_blueprint_class,
    is_projected_blueprint,
)

# Check if a class is a Blueprint
is_blueprint_class(ProductBlueprint)  # True
is_blueprint_class(str)                # False

# Check if it's a projected Blueprint reference
is_projected_blueprint(ProductBlueprint["summary"])  # True

# Resolve Blueprint from a type annotation
bp_class = resolve_blueprint_from_annotation(handler_param_annotation)
# Returns (BlueprintClass, projection_name) or None

# Bind Blueprint to an incoming request (used internally by controller engine)
bp = await bind_blueprint_to_request(ProductBlueprint, request, container)

# Render model data through Blueprint for response
data = render_blueprint_response(ProductBlueprint, instance, projection="summary")`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
