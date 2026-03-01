import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { FileCheck } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function BlueprintsSeals() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <FileCheck className="w-4 h-4" />
          Blueprints / Seals & Validation
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Seals & Validation
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Sealing is Aquilia's term for validation. The <code className="text-aquilia-500">is_sealed()</code> method runs a multi-phase pipeline that progressively validates data — from raw type coercion through field constraints, cross-field rules, and async database checks.
        </p>
      </div>

      {/* Validation Pipeline */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>The Sealing Pipeline</h2>
        <div className="space-y-3">
          {[
            { phase: 'Phase 1', name: 'Cast', desc: 'Each Facet coerces its raw input to the expected Python type. Failures produce CastFault.' },
            { phase: 'Phase 2', name: 'Field Seals', desc: 'Each Facet runs its own seal() method — checking min/max, patterns, required, etc.' },
            { phase: 'Phase 3', name: 'Cross-field Seals', desc: 'Methods named seal_*(data) receive the full validated dict for cross-field rules.' },
            { phase: 'Phase 4', name: 'validate()', desc: 'Final synchronous hook for object-level validation. Can transform data.' },
            { phase: 'Phase 5', name: 'Async Seals', desc: 'Methods named async_seal_*(data) for I/O-bound checks (uniqueness, external API, etc.)' },
          ].map((item, i) => (
            <div key={i} className={boxClass}>
              <div className="flex items-center gap-3">
                <span className="text-aquilia-500 font-mono font-bold text-sm">{item.phase}</span>
                <code className={`font-bold text-sm ${isDark ? 'text-white' : 'text-gray-900'}`}>{item.name}</code>
              </div>
              <p className={`text-sm mt-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* is_sealed() vs is_sealed_async() */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Sync vs Async Validation</h2>
        <CodeBlock language="python" filename="sync_async.py">{`bp = RegisterBlueprint(data=request_body)

# Sync validation (Phases 1-4 only)
if bp.is_sealed():
    user = bp.imprint()
else:
    return ctx.json(bp.errors, status=422)

# Async validation (Phases 1-5 — includes async_seal_* methods)
if await bp.is_sealed_async():
    user = bp.imprint()
else:
    return ctx.json(bp.errors, status=422)

# With raise_fault=True, validation errors raise SealFault instead of returning False
try:
    bp.is_sealed(raise_fault=True)
except SealFault as e:
    return ctx.json(e.as_response_body(), status=422)`}</CodeBlock>
      </section>

      {/* Field-Level Validation */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Field-Level Validation</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Facets validate their own values automatically during Phase 2. You can also define per-field seal methods:
        </p>
        <CodeBlock language="python" filename="field_seals.py">{`class ProductBlueprint(Blueprint):
    name = TextFacet(max_length=200)
    price = FloatFacet(min_value=0)
    sku = TextFacet(max_length=50, pattern=r"^[A-Z0-9-]+$")

    class Spec:
        model = Product
        fields = ["name", "price", "sku"]

    # Per-field seal method — naming convention: seal_{field_name}
    def seal_name(self, value):
        """Validate the 'name' field specifically."""
        if "forbidden" in value.lower():
            self.reject("name", "Product name contains forbidden word.")
        return value.strip().title()  # Return transformed value

    def seal_sku(self, value):
        """Ensure SKU follows company format."""
        if not value.startswith("AQ-"):
            self.reject("sku", "SKU must start with 'AQ-'.")
        return value.upper()


# Built-in Facet validations (automatic):
# TextFacet:    max_length, min_length, pattern, trim
# IntFacet:     min_value, max_value, boolean rejection
# FloatFacet:   min_value, max_value
# DecimalFacet: max_digits, decimal_places
# EmailFacet:   email regex
# URLFacet:     URL regex
# SlugFacet:    alphanumeric + hyphens
# IPFacet:      ipaddress validation
# ListFacet:    min_items, max_items, per-item validation
# ChoiceFacet:  value in choices`}</CodeBlock>
      </section>

      {/* Cross-Field Validation */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Cross-Field Validation</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Cross-field seals receive the entire validated data dictionary and can enforce rules that span multiple fields:
        </p>
        <CodeBlock language="python" filename="cross_field.py">{`class EventBlueprint(Blueprint):
    title = TextFacet(max_length=200)
    start_date = DateTimeFacet()
    end_date = DateTimeFacet()
    min_attendees = IntFacet(min_value=1)
    max_attendees = IntFacet(min_value=1)
    registration_deadline = DateTimeFacet()

    class Spec:
        model = Event
        fields = "__all__"

    # Cross-field seals — naming convention: seal_{descriptive_name}
    def seal_date_range(self, data):
        """Ensure end_date is after start_date."""
        if data.get("start_date") and data.get("end_date"):
            if data["end_date"] <= data["start_date"]:
                self.reject("end_date", "End date must be after start date.")

    def seal_attendee_range(self, data):
        """Ensure max >= min attendees."""
        min_att = data.get("min_attendees", 0)
        max_att = data.get("max_attendees", 0)
        if max_att < min_att:
            self.reject("max_attendees", "Maximum must be >= minimum attendees.")

    def seal_registration_deadline(self, data):
        """Deadline must be before event start."""
        deadline = data.get("registration_deadline")
        start = data.get("start_date")
        if deadline and start and deadline >= start:
            self.reject("registration_deadline", "Registration must close before event starts.")`}</CodeBlock>
      </section>

      {/* Async Validation */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Async Validation</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Async seals are perfect for I/O-bound validation — database uniqueness checks, external API verification, etc. They only run when using <code className="text-aquilia-500">is_sealed_async()</code>:
        </p>
        <CodeBlock language="python" filename="async_seals.py">{`class RegisterBlueprint(Blueprint):
    username = TextFacet(min_length=3, max_length=30)
    email = EmailFacet(required=True)
    domain = TextFacet(max_length=100)

    class Spec:
        model = User
        fields = ["username", "email", "domain"]

    # Async seal — naming convention: async_seal_{descriptive_name}
    async def async_seal_email_unique(self, data):
        """Check email uniqueness in database."""
        exists = await User.objects.filter(email=data["email"]).exists()
        if exists:
            self.reject("email", "This email is already registered.")

    async def async_seal_username_unique(self, data):
        """Check username uniqueness."""
        exists = await User.objects.filter(username=data["username"]).exists()
        if exists:
            self.reject("username", "This username is already taken.")

    async def async_seal_domain_valid(self, data):
        """Verify domain has valid MX records (external API call)."""
        import aiohttp
        async with aiohttp.ClientSession() as session:
            resp = await session.get(f"https://api.mailcheck.ai/domain/{data['domain']}")
            result = await resp.json()
            if not result.get("valid"):
                self.reject("domain", "Invalid email domain.")`}</CodeBlock>
      </section>

      {/* validate() Hook */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>The validate() Hook</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">validate()</code> method is the final sync hook. Use it for data transformation or last-resort validation:
        </p>
        <CodeBlock language="python" filename="validate_hook.py">{`class RegisterBlueprint(Blueprint):
    username = TextFacet(min_length=3, max_length=30)
    email = EmailFacet()
    password = TextFacet(min_length=8)
    password_confirm = TextFacet(min_length=8)

    class Spec:
        model = User
        fields = ["username", "email", "password"]

    def validate(self, data):
        """
        Final validation hook. Receives fully validated data dict.
        Can modify and return transformed data.
        """
        # Remove confirmation field (not a model field)
        data.pop("password_confirm", None)
        
        # Hash the password before imprint
        from aquilia.auth import hash_password
        data["password"] = hash_password(data["password"])
        
        return data


# validate() runs AFTER all seal_* methods
# It can:
# - Remove transient fields
# - Transform values
# - Add computed data
# - Raise SealFault for final checks`}</CodeBlock>
      </section>

      {/* reject() API */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>The reject() Method</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <code className="text-aquilia-500">self.reject(field, message)</code> is the preferred way to add validation errors. It accumulates errors rather than raising immediately:
        </p>
        <CodeBlock language="python" filename="reject.py">{`class OrderBlueprint(Blueprint):
    items = ListFacet(child=IntFacet())
    coupon_code = TextFacet(required=False)

    def seal_order(self, data):
        # Multiple rejections are accumulated
        if not data.get("items"):
            self.reject("items", "At least one item is required.")
        
        if len(data.get("items", [])) > 100:
            self.reject("items", "Maximum 100 items per order.")
        
        if data.get("coupon_code") and not is_valid_coupon(data["coupon_code"]):
            self.reject("coupon_code", "Invalid or expired coupon.")


# Errors are accumulated in bp.errors:
bp = OrderBlueprint(data={"items": [], "coupon_code": "EXPIRED"})
bp.is_sealed()
print(bp.errors)
# {
#   "items": ["At least one item is required."],
#   "coupon_code": ["Invalid or expired coupon."]
# }`}</CodeBlock>
      </section>

      {/* Custom Validators */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Custom Validator Functions</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          You can pass reusable validator functions to any Facet via the <code className="text-aquilia-500">validators</code> parameter:
        </p>
        <CodeBlock language="python" filename="custom_validators.py">{`def no_profanity(value):
    """Reusable validator — raises SealFault on bad words."""
    bad_words = ["spam", "hack"]
    for word in bad_words:
        if word in value.lower():
            from aquilia.blueprints.exceptions import SealFault
            raise SealFault(field="value", message=f"Contains forbidden word: {word}")
    return value


def min_words(count):
    """Validator factory — ensures minimum word count."""
    def validator(value):
        if len(value.split()) < count:
            from aquilia.blueprints.exceptions import SealFault
            raise SealFault(field="value", message=f"Must contain at least {count} words.")
        return value
    return validator


class ArticleBlueprint(Blueprint):
    title = TextFacet(max_length=200, validators=[no_profanity])
    body = TextFacet(max_length=10000, validators=[no_profanity, min_words(50)])
    
    class Spec:
        model = Article
        fields = ["title", "body"]`}</CodeBlock>
      </section>

      {/* Partial Validation */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Partial Validation (PATCH Updates)</h2>
        <CodeBlock language="python" filename="partial.py">{`# For PATCH requests, use partial=True to skip required checks on missing fields
bp = ProductBlueprint(data={"price": 14.99}, partial=True)

if bp.is_sealed():
    # Only validates and updates the provided fields
    bp.imprint(instance=existing_product, partial=True)
    await existing_product.save()

# Without partial=True, missing required fields would cause SealFault`}</CodeBlock>
      </section>

      {/* Error Format */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Error Format</h2>
        <CodeBlock language="python" filename="errors.py">{`bp = RegisterBlueprint(data={
    "username": "x",
    "email": "not-an-email",
    "password": "short",
    "password_confirm": "different"
})
bp.is_sealed()

# bp.errors contains field → list of messages
print(bp.errors)
# {
#   "username": ["Must be at least 3 characters."],
#   "email": ["Invalid email format."],
#   "password": ["Must be at least 8 characters."],
#   "password_confirm": ["Passwords do not match."]
# }

# SealFault.as_response_body() for structured API response:
# {
#   "fault_code": "BP200",
#   "fault_domain": "BLUEPRINT",
#   "message": "Validation failed",
#   "field_errors": { ... }
# }`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
