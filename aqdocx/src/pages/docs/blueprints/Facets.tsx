import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Layers } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function BlueprintsFacets() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Layers className="w-4 h-4" />
          Blueprints / Facets
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Facets
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Facets are the atomic field-level primitives of a Blueprint. Each Facet handles its own type coercion (cast), validation (seal), and output transformation (mold). Aquilia ships with 25+ built-in Facet types covering text, numeric, date/time, structured, and special-purpose fields.
        </p>
      </div>

      {/* Base Facet */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Base Facet</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          All Facets inherit from <code className="text-aquilia-500">Facet</code>, which provides the common lifecycle and configuration options:
        </p>
        <CodeBlock language="python" filename="base_facet.py">{`from aquilia.blueprints import Facet

# Every Facet supports these common options:
field = Facet(
    source="model_field_name",  # Model attribute to read from (default: field name)
    required=True,              # Required in input (default: True)
    read_only=False,            # Exclude from input, include in output
    write_only=False,           # Include in input, exclude from output
    default=None,               # Default value if not provided
    allow_null=False,           # Allow None values
    allow_blank=False,          # Allow empty strings (TextFacet)
    label="Human Label",        # Display label for docs
    help_text="Description",    # Help text for docs/OpenAPI
    validators=[],              # Additional validator callables
)`}</CodeBlock>

        <h3 className={`text-lg font-bold mt-8 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Facet Lifecycle</h3>
        <div className={boxClass}>
          <div className={`font-mono text-xs space-y-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <div><code className="text-aquilia-500">cast(value)</code> — Coerce raw input to Python type (e.g., str → int)</div>
            <div><code className="text-aquilia-500">seal(value)</code> — Validate the casted value against constraints</div>
            <div><code className="text-aquilia-500">mold(value)</code> — Transform Python value for JSON output</div>
            <div><code className="text-aquilia-500">extract(instance)</code> — Read value from Model instance</div>
            <div><code className="text-aquilia-500">to_schema()</code> — Generate JSON Schema for this field</div>
            <div><code className="text-aquilia-500">bind(name, blueprint)</code> — Bind Facet to a Blueprint (sets context)</div>
            <div><code className="text-aquilia-500">clone(**overrides)</code> — Create a copy with overridden settings</div>
          </div>
        </div>
      </section>

      {/* Text Facets */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Text Facets</h2>

        <h3 className={`text-lg font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>TextFacet</h3>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The most common Facet. Handles string data with length constraints, regex patterns, and optional trimming.
        </p>
        <CodeBlock language="python" filename="text_facets.py">{`from aquilia.blueprints import TextFacet

# Basic text field
name = TextFacet(max_length=200, required=True)

# With regex pattern
sku = TextFacet(max_length=50, pattern=r"^[A-Z0-9-]+$")

# Auto-trimming whitespace (default: True)
title = TextFacet(max_length=100, trim=True)

# Allow blank strings
notes = TextFacet(max_length=2000, allow_blank=True, required=False)

# Options:
#   max_length: int     — Maximum string length
#   min_length: int     — Minimum string length (default: 0)
#   trim: bool          — Strip whitespace (default: True)
#   pattern: str        — Regex pattern to match`}</CodeBlock>

        <h3 className={`text-lg font-bold mt-8 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>EmailFacet</h3>
        <CodeBlock language="python" filename="email_facet.py">{`from aquilia.blueprints import EmailFacet

email = EmailFacet(required=True)

# Cast behavior:
#   "User@Example.COM" → "user@example.com"  (auto-lowercased)
#
# Seal behavior:
#   Validates against email regex pattern
#   Rejects malformed addresses`}</CodeBlock>

        <h3 className={`text-lg font-bold mt-8 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>URLFacet</h3>
        <CodeBlock language="python" filename="url_facet.py">{`from aquilia.blueprints import URLFacet

website = URLFacet(required=False)

# Validates against URL regex pattern
# Accepts: http://, https://, ftp:// etc.`}</CodeBlock>

        <h3 className={`text-lg font-bold mt-8 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>SlugFacet</h3>
        <CodeBlock language="python" filename="slug_facet.py">{`from aquilia.blueprints import SlugFacet

slug = SlugFacet(max_length=100)

# Only allows: lowercase letters, numbers, hyphens
# "my-awesome-product" ✓
# "My Product!"        ✗`}</CodeBlock>

        <h3 className={`text-lg font-bold mt-8 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>IPFacet</h3>
        <CodeBlock language="python" filename="ip_facet.py">{`from aquilia.blueprints import IPFacet

ip_address = IPFacet()

# Validates using Python's ipaddress module
# Accepts both IPv4 and IPv6
# "192.168.1.1"     ✓
# "::1"             ✓
# "not-an-ip"       ✗`}</CodeBlock>
      </section>

      {/* Numeric Facets */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Numeric Facets</h2>

        <h3 className={`text-lg font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>IntFacet</h3>
        <CodeBlock language="python" filename="int_facet.py">{`from aquilia.blueprints import IntFacet

quantity = IntFacet(min_value=1, max_value=9999)

# Cast behavior:
#   "42" → 42            (string coercion)
#   42.0 → 42            (float truncation)
#   True → REJECTED       (booleans are NOT valid ints in Aquilia!)
#
# Options:
#   min_value: int | None — Minimum allowed value
#   max_value: int | None — Maximum allowed value`}</CodeBlock>

        <h3 className={`text-lg font-bold mt-8 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>FloatFacet</h3>
        <CodeBlock language="python" filename="float_facet.py">{`from aquilia.blueprints import FloatFacet

price = FloatFacet(min_value=0)

# Cast: "19.99" → 19.99
# Options: min_value, max_value`}</CodeBlock>

        <h3 className={`text-lg font-bold mt-8 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>DecimalFacet</h3>
        <CodeBlock language="python" filename="decimal_facet.py">{`from aquilia.blueprints import DecimalFacet

amount = DecimalFacet(max_digits=10, decimal_places=2)

# Cast: "199.99" → Decimal("199.99")
# Mold: Decimal("199.99") → "199.99"  (string for JSON precision)
#
# Options:
#   max_digits: int       — Total digits allowed
#   decimal_places: int   — Digits after decimal point`}</CodeBlock>
      </section>

      {/* Boolean */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>BoolFacet</h2>
        <CodeBlock language="python" filename="bool_facet.py">{`from aquilia.blueprints import BoolFacet

is_active = BoolFacet(default=True)

# Smart coercion from strings:
#   "true", "yes", "1", "on"   → True
#   "false", "no", "0", "off"  → False
#   True / False                → pass through`}</CodeBlock>
      </section>

      {/* Date/Time Facets */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Date & Time Facets</h2>
        <CodeBlock language="python" filename="datetime_facets.py">{`from aquilia.blueprints import DateFacet, TimeFacet, DateTimeFacet, DurationFacet, UUIDFacet

# DateFacet — ISO 8601 date
birth_date = DateFacet()
# Cast: "2024-03-15" → date(2024, 3, 15)
# Mold: date → "2024-03-15"

# TimeFacet — ISO 8601 time
start_time = TimeFacet()
# Cast: "14:30:00" → time(14, 30, 0)

# DateTimeFacet — ISO 8601 datetime
created_at = DateTimeFacet(read_only=True)
# Cast: "2024-03-15T14:30:00Z" → datetime(...)
# Mold: datetime → ISO string

# DurationFacet — Duration
timeout = DurationFacet()
# Cast: 3600 → timedelta(seconds=3600)
# Cast: "01:30:00" → timedelta(hours=1, minutes=30)

# UUIDFacet — UUID
ref = UUIDFacet()
# Cast: "550e8400-e29b-41d4-a716-446655440000" → UUID(...)
# Mold: UUID → string`}</CodeBlock>
      </section>

      {/* Structured Facets */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Structured Facets</h2>

        <h3 className={`text-lg font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>ListFacet</h3>
        <CodeBlock language="python" filename="list_facet.py">{`from aquilia.blueprints import ListFacet, TextFacet, IntFacet

# List of strings
tags = ListFacet(child=TextFacet(max_length=50))

# List of integers with size constraints
scores = ListFacet(
    child=IntFacet(min_value=0, max_value=100),
    min_items=1,
    max_items=10,
)

# Each child element is individually cast and sealed`}</CodeBlock>

        <h3 className={`text-lg font-bold mt-8 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>DictFacet</h3>
        <CodeBlock language="python" filename="dict_facet.py">{`from aquilia.blueprints import DictFacet, TextFacet

# Typed dictionary values
metadata = DictFacet(value_facet=TextFacet())

# Untyped dictionary (any JSON values)
settings = DictFacet()`}</CodeBlock>

        <h3 className={`text-lg font-bold mt-8 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>JSONFacet</h3>
        <CodeBlock language="python" filename="json_facet.py">{`from aquilia.blueprints import JSONFacet

# Accepts any valid JSON value (object, array, string, number, etc.)
payload = JSONFacet()

# Useful for schemaless data or dynamic payloads`}</CodeBlock>

        <h3 className={`text-lg font-bold mt-8 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>FileFacet</h3>
        <CodeBlock language="python" filename="file_facet.py">{`from aquilia.blueprints import FileFacet

# Accepts file path or URL string
avatar = FileFacet(required=False)`}</CodeBlock>
      </section>

      {/* Choice & Polymorphic */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Choice & Polymorphic Facets</h2>

        <h3 className={`text-lg font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>ChoiceFacet</h3>
        <CodeBlock language="python" filename="choice_facet.py">{`from aquilia.blueprints import ChoiceFacet

# List of allowed values
status = ChoiceFacet(choices=["draft", "published", "archived"])

# Dict choices (value → display label)
priority = ChoiceFacet(choices={
    "low": "Low Priority",
    "medium": "Medium Priority",
    "high": "High Priority",
})

# Tuple choices (Django-style)
role = ChoiceFacet(choices=[
    ("admin", "Administrator"),
    ("editor", "Content Editor"),
    ("viewer", "Read-Only Viewer"),
])`}</CodeBlock>

        <h3 className={`text-lg font-bold mt-8 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>PolymorphicFacet</h3>
        <CodeBlock language="python" filename="polymorphic_facet.py">{`from aquilia.blueprints import PolymorphicFacet, TextFacet, IntFacet

# Union type — tries each candidate in order
flexible_id = PolymorphicFacet(candidates=[
    TextFacet(),   # Try string first
    IntFacet(),    # Then integer
])

# Cast: "abc" → "abc" (TextFacet succeeds)
# Cast: 42    → 42    (IntFacet succeeds)
# Cast: []    → CastFault (all candidates fail)`}</CodeBlock>
      </section>

      {/* Special Facets */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Special Facets</h2>

        <h3 className={`text-lg font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Computed</h3>
        <CodeBlock language="python" filename="computed_facet.py">{`from aquilia.blueprints import Blueprint, Computed, TextFacet

class UserBlueprint(Blueprint):
    first_name = TextFacet()
    last_name = TextFacet()
    
    # Computed field — read-only, derived from other data
    full_name = Computed(lambda instance: f"{instance.first_name} {instance.last_name}")

    class Spec:
        model = User
        fields = ["first_name", "last_name"]

# Output: {"first_name": "John", "last_name": "Doe", "full_name": "John Doe"}
# Input: full_name is NEVER accepted in input`}</CodeBlock>

        <h3 className={`text-lg font-bold mt-8 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Constant</h3>
        <CodeBlock language="python" filename="constant_facet.py">{`from aquilia.blueprints import Blueprint, Constant

class AnimalBlueprint(Blueprint):
    # Type discriminator — always outputs "animal", rejects other input
    type = Constant(value="animal")

class DogBlueprint(AnimalBlueprint):
    type = Constant(value="dog")

# Useful for polymorphic API responses with type discrimination`}</CodeBlock>

        <h3 className={`text-lg font-bold mt-8 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>WriteOnly & ReadOnly</h3>
        <CodeBlock language="python" filename="writeonly_readonly.py">{`from aquilia.blueprints import WriteOnly, ReadOnly

class UserBlueprint(Blueprint):
    email = EmailFacet()
    
    # WriteOnly — accepted in input, never in output (passwords, secrets)
    password = WriteOnly()
    
    # ReadOnly — only in output, auto-serializes dates/UUIDs/Decimals
    created_at = ReadOnly()
    last_login = ReadOnly()

    class Spec:
        model = User
        fields = ["email", "password", "created_at", "last_login"]`}</CodeBlock>

        <h3 className={`text-lg font-bold mt-8 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Hidden & Inject</h3>
        <CodeBlock language="python" filename="hidden_inject.py">{`from aquilia.blueprints import Blueprint, Hidden, Inject

class AuditBlueprint(Blueprint):
    # Hidden — populated by DI, never appears in I/O
    created_by = Hidden()

    # Inject — resolves from DI container
    audit_service = Inject(token="AuditService")
    
    # Inject with specific attribute
    current_user_id = Inject(via="request", attr="user.id")

# Hidden fields are stripped from both input and output
# Inject fields resolve dependencies at Blueprint creation time`}</CodeBlock>
      </section>

      {/* Complete Reference Table */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Complete Reference</h2>
        <div className={`overflow-hidden rounded-xl border ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={isDark ? 'bg-zinc-900' : 'bg-gray-50'}>
                <th className={`text-left py-3 px-4 font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Facet</th>
                <th className={`text-left py-3 px-4 font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Python Type</th>
                <th className={`text-left py-3 px-4 font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Key Options</th>
              </tr>
            </thead>
            <tbody className={isDark ? 'divide-y divide-white/5' : 'divide-y divide-gray-100'}>
              {[
                { f: 'TextFacet', t: 'str', o: 'max_length, min_length, pattern, trim' },
                { f: 'EmailFacet', t: 'str', o: 'auto-lowercase, regex validation' },
                { f: 'URLFacet', t: 'str', o: 'URL regex validation' },
                { f: 'SlugFacet', t: 'str', o: 'alphanumeric + hyphens only' },
                { f: 'IPFacet', t: 'str', o: 'IPv4/IPv6 via ipaddress module' },
                { f: 'IntFacet', t: 'int', o: 'min_value, max_value (rejects booleans)' },
                { f: 'FloatFacet', t: 'float', o: 'min_value, max_value' },
                { f: 'DecimalFacet', t: 'Decimal', o: 'max_digits, decimal_places' },
                { f: 'BoolFacet', t: 'bool', o: 'truthy/falsy string coercion' },
                { f: 'DateFacet', t: 'date', o: 'ISO 8601 parsing' },
                { f: 'TimeFacet', t: 'time', o: 'ISO 8601 parsing' },
                { f: 'DateTimeFacet', t: 'datetime', o: 'ISO 8601 parsing' },
                { f: 'DurationFacet', t: 'timedelta', o: 'seconds or HH:MM:SS' },
                { f: 'UUIDFacet', t: 'UUID', o: 'string ↔ UUID conversion' },
                { f: 'ListFacet', t: 'list', o: 'child, min_items, max_items' },
                { f: 'DictFacet', t: 'dict', o: 'value_facet for typed values' },
                { f: 'JSONFacet', t: 'Any', o: 'any valid JSON value' },
                { f: 'FileFacet', t: 'str', o: 'file path or URL string' },
                { f: 'ChoiceFacet', t: 'Any', o: 'list/dict/tuple choices' },
                { f: 'PolymorphicFacet', t: 'Union', o: 'candidates list of Facets' },
                { f: 'Computed', t: 'Any', o: 'lambda/method, read-only output' },
                { f: 'Constant', t: 'Any', o: 'fixed value, type discriminator' },
                { f: 'WriteOnly', t: 'str', o: 'input only (passwords, secrets)' },
                { f: 'ReadOnly', t: 'Any', o: 'output only (auto-serializes)' },
                { f: 'Hidden', t: 'Any', o: 'DI-populated, never in I/O' },
                { f: 'Inject', t: 'Any', o: 'token, via, attr (DI resolution)' },
              ].map((row, i) => (
                <tr key={i} className={isDark ? 'bg-[#0A0A0A]' : 'bg-white'}>
                  <td className="py-2 px-4"><code className="text-aquilia-500 font-mono text-xs">{row.f}</code></td>
                  <td className={`py-2 px-4 font-mono text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{row.t}</td>
                  <td className={`py-2 px-4 text-xs ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>{row.o}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <NextSteps />
    </div>
  )
}
