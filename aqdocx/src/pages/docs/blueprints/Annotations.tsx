import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Sparkles } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function BlueprintsAnnotations() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Sparkles className="w-4 h-4" />
          Blueprints / Annotations & Field()
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Annotations & Field()
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          As an alternative to explicit Facet declarations, Aquilia supports type-annotation-driven Blueprints using the <code className="text-aquilia-500">Field</code> descriptor. Write Pythonic type hints and let the metaclass derive the correct Facets automatically.
        </p>
      </div>

      {/* Two Declaration Styles */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Two Declaration Styles</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className={boxClass}>
            <h3 className={`font-bold text-sm mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Explicit Facets</h3>
            <p className={`text-xs mb-3 ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>Full control, more verbose</p>
            <CodeBlock language="python">{`class UserBP(Blueprint):
    name = TextFacet(max_length=100)
    age = IntFacet(min_value=0)
    email = EmailFacet()`}</CodeBlock>
          </div>
          <div className={boxClass}>
            <h3 className={`font-bold text-sm mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Type Annotations</h3>
            <p className={`text-xs mb-3 ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>Pythonic, concise, auto-derived</p>
            <CodeBlock language="python">{`class UserBP(Blueprint):
    name: str = Field(max_length=100)
    age: int = Field(ge=0)
    email: str = Field()`}</CodeBlock>
          </div>
        </div>
        <p className={`mt-4 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Both styles produce identical Blueprint behavior. You can even mix them in the same Blueprint — explicit Facets take priority over annotation-derived ones.
        </p>
      </section>

      {/* Field() Descriptor */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>The Field() Descriptor</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <code className="text-aquilia-500">Field</code> is a constraint descriptor that decorates type annotations with validation rules:
        </p>
        <CodeBlock language="python" filename="field_descriptor.py">{`from aquilia.blueprints import Blueprint, Field


class ProductBlueprint(Blueprint):
    # All Field() options:
    name: str = Field(
        default=None,           # Default value if not provided
        required=True,          # Is this field required in input?
        read_only=False,        # Exclude from input, include in output
        write_only=False,       # Include in input, exclude from output
        allow_null=False,       # Allow None values
        
        # Numeric constraints (maps to min_value/max_value)
        ge=0,                   # Greater than or equal to
        le=100,                 # Less than or equal to
        gt=None,                # Greater than (strict)
        lt=None,                # Less than (strict)
        
        # String constraints
        min_length=None,        # Minimum string length
        max_length=200,         # Maximum string length
        pattern=None,           # Regex pattern
        
        # Collection constraints
        min_items=None,         # Minimum list items
        max_items=None,         # Maximum list items
        
        # Choice constraint
        choices=None,           # Allowed values (list/dict/tuple)
        
        # Decimal constraints
        max_digits=None,        # Total digits (DecimalFacet)
        decimal_places=None,    # Decimal places (DecimalFacet)
        
        # Source mapping
        alias=None,             # Alternative name in input JSON
    )

    class Spec:
        model = Product
        fields = "__all__"`}</CodeBlock>
      </section>

      {/* Type Annotation Mapping */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Type → Facet Mapping</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">introspect_annotations()</code> system maps Python type annotations to the appropriate Facet class:
        </p>
        <div className={`overflow-hidden rounded-xl border ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={isDark ? 'bg-zinc-900' : 'bg-gray-50'}>
                <th className={`text-left py-3 px-4 font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Type Annotation</th>
                <th className={`text-left py-3 px-4 font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Derived Facet</th>
              </tr>
            </thead>
            <tbody className={isDark ? 'divide-y divide-white/5' : 'divide-y divide-gray-100'}>
              {[
                { ann: 'str', facet: 'TextFacet' },
                { ann: 'int', facet: 'IntFacet' },
                { ann: 'float', facet: 'FloatFacet' },
                { ann: 'bool', facet: 'BoolFacet' },
                { ann: 'Decimal', facet: 'DecimalFacet' },
                { ann: 'date', facet: 'DateFacet' },
                { ann: 'time', facet: 'TimeFacet' },
                { ann: 'datetime', facet: 'DateTimeFacet' },
                { ann: 'timedelta', facet: 'DurationFacet' },
                { ann: 'UUID', facet: 'UUIDFacet' },
                { ann: 'list[str]', facet: 'ListFacet(child=TextFacet())' },
                { ann: 'list[int]', facet: 'ListFacet(child=IntFacet())' },
                { ann: 'dict', facet: 'DictFacet' },
                { ann: 'Optional[str]', facet: 'TextFacet(allow_null=True)' },
                { ann: 'str | None', facet: 'TextFacet(allow_null=True)' },
                { ann: 'UserBlueprint', facet: 'NestedBlueprintFacet(UserBlueprint)' },
                { ann: 'list[UserBlueprint]', facet: 'NestedBlueprintFacet(UserBlueprint, many=True)' },
                { ann: '"UserBlueprint"', facet: 'LazyBlueprintFacet("UserBlueprint")' },
                { ann: 'str | int', facet: 'PolymorphicFacet(...)' },
              ].map((row, i) => (
                <tr key={i} className={isDark ? 'bg-[#0A0A0A]' : 'bg-white'}>
                  <td className="py-2 px-4"><code className="text-aquilia-500 font-mono text-xs">{row.ann}</code></td>
                  <td className={`py-2 px-4 font-mono text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{row.facet}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Practical Examples */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Practical Examples</h2>

        <h3 className={`text-lg font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>User Registration</h3>
        <CodeBlock language="python" filename="registration.py">{`from aquilia.blueprints import Blueprint, Field
from datetime import date


class RegisterBlueprint(Blueprint):
    username: str = Field(min_length=3, max_length=30)
    email: str = Field(required=True)              # Becomes EmailFacet? No — str → TextFacet
    password: str = Field(min_length=8, write_only=True)
    birth_date: date = Field(required=False)
    age: int = Field(ge=13, le=120, required=False)
    
    class Spec:
        model = User
        fields = ["username", "email", "password", "birth_date"]`}</CodeBlock>

        <h3 className={`text-lg font-bold mt-8 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>E-Commerce Order</h3>
        <CodeBlock language="python" filename="order.py">{`from aquilia.blueprints import Blueprint, Field
from decimal import Decimal
from uuid import UUID
from typing import Optional


class OrderItemBlueprint(Blueprint):
    product_id: int = Field(required=True)
    quantity: int = Field(ge=1, le=999)
    unit_price: Decimal = Field(max_digits=10, decimal_places=2)
    note: Optional[str] = Field(max_length=500)   # allow_null=True auto-set

    class Spec:
        model = OrderItem
        fields = "__all__"


class OrderBlueprint(Blueprint):
    reference: UUID = Field(read_only=True)
    customer_name: str = Field(max_length=200)
    items: list[OrderItemBlueprint] = Field(min_items=1)  # Nested Blueprint
    total: Decimal = Field(max_digits=12, decimal_places=2, read_only=True)
    status: str = Field(choices=["pending", "confirmed", "shipped", "delivered"])

    class Spec:
        model = Order
        fields = "__all__"
        read_only_fields = ["reference", "total"]`}</CodeBlock>
      </section>

      {/* @computed Decorator */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>The @computed Decorator</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Mark methods as computed output fields using <code className="text-aquilia-500">@computed</code>. These fields appear in output but never accept input:
        </p>
        <CodeBlock language="python" filename="computed.py">{`from aquilia.blueprints import Blueprint, Field, computed


class UserBlueprint(Blueprint):
    first_name: str = Field(max_length=50)
    last_name: str = Field(max_length=50)
    email: str = Field()
    avatar_url: str = Field(read_only=True)

    class Spec:
        model = User
        fields = ["first_name", "last_name", "email", "avatar_url"]

    @computed
    def full_name(self, instance):
        """Computed from first + last name."""
        return f"{instance.first_name} {instance.last_name}"

    @computed
    def initials(self, instance):
        """First letter of each name part."""
        return "".join(
            part[0].upper()
            for part in f"{instance.first_name} {instance.last_name}".split()
        )

    @computed
    def gravatar_url(self, instance):
        """Generate gravatar URL from email."""
        import hashlib
        email_hash = hashlib.md5(instance.email.lower().encode()).hexdigest()
        return f"https://gravatar.com/avatar/{email_hash}"


# Output:
# {
#   "first_name": "Alice",
#   "last_name": "Smith",
#   "email": "alice@example.com",
#   "avatar_url": "...",
#   "full_name": "Alice Smith",
#   "initials": "AS",
#   "gravatar_url": "https://gravatar.com/avatar/..."
# }`}</CodeBlock>
      </section>

      {/* Nested Blueprints */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Nested Blueprints via Annotations</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          When you annotate a field with another Blueprint class, Aquilia creates a <code className="text-aquilia-500">NestedBlueprintFacet</code> that delegates validation to the nested Blueprint:
        </p>
        <CodeBlock language="python" filename="nested.py">{`class AddressBlueprint(Blueprint):
    street: str = Field(max_length=200)
    city: str = Field(max_length=100)
    zip_code: str = Field(max_length=20)
    country: str = Field(max_length=100, default="US")

    class Spec:
        model = Address
        fields = "__all__"


class CompanyBlueprint(Blueprint):
    name: str = Field(max_length=200)
    
    # Single nested Blueprint
    headquarters: AddressBlueprint = Field(required=True)
    
    # List of nested Blueprints
    offices: list[AddressBlueprint] = Field(required=False)

    class Spec:
        model = Company
        fields = "__all__"


# Input:
# {
#   "name": "Aquilia Corp",
#   "headquarters": {"street": "123 Main", "city": "NYC", "zip_code": "10001"},
#   "offices": [
#     {"street": "456 Oak", "city": "LA", "zip_code": "90001"},
#   ]
# }
# Each nested object is validated through AddressBlueprint.is_sealed()`}</CodeBlock>
      </section>

      {/* Forward References */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Lazy Forward References</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          For circular references, use string annotations. Aquilia resolves them lazily from the Blueprint registry:
        </p>
        <CodeBlock language="python" filename="lazy_ref.py">{`from __future__ import annotations  # Enable PEP 563

class DepartmentBlueprint(Blueprint):
    name: str = Field(max_length=100)
    
    # Forward reference — EmployeeBlueprint not yet defined
    manager: "EmployeeBlueprint" = Field(required=False)
    employees: list["EmployeeBlueprint"] = Field(required=False)

    class Spec:
        model = Department
        fields = "__all__"


class EmployeeBlueprint(Blueprint):
    name: str = Field(max_length=100)
    department: DepartmentBlueprint = Field()  # Direct reference (already defined)

    class Spec:
        model = Employee
        fields = "__all__"


# Both resolve correctly at runtime via _blueprint_registry`}</CodeBlock>
      </section>

      {/* Optional & Union */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Optional & Union Types</h2>
        <CodeBlock language="python" filename="optional_union.py">{`from typing import Optional, Union


class FlexibleBlueprint(Blueprint):
    # Optional — allows null
    nickname: Optional[str] = Field(max_length=50)
    # Same as: str | None = Field(...)
    # Produces: TextFacet(allow_null=True, max_length=50)

    # Union — polymorphic
    identifier: str | int = Field()
    # Produces: PolymorphicFacet(candidates=[TextFacet(), IntFacet()])
    # Tries str first, then int

    class Spec:
        model = Flexible
        fields = "__all__"`}</CodeBlock>
      </section>

      {/* PEP 563 Support */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>PEP 563 / 649 Support</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia's <code className="text-aquilia-500">introspect_annotations()</code> fully supports deferred evaluation of annotations via <code className="text-aquilia-500">from __future__ import annotations</code> (PEP 563). String annotations are resolved against the module's globals at Blueprint class creation time.
        </p>
        <CodeBlock language="python" filename="pep563.py">{`from __future__ import annotations  # All annotations become strings

from datetime import datetime
from decimal import Decimal


class InvoiceBlueprint(Blueprint):
    # These are string annotations at parse time,
    # resolved to actual types by introspect_annotations()
    amount: Decimal = Field(max_digits=10, decimal_places=2)
    issued_at: datetime = Field(read_only=True)
    notes: str | None = Field(max_length=500)

    class Spec:
        model = Invoice
        fields = "__all__"`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
