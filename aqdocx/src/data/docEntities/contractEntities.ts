import { registerDocEntities } from '../../lib/docPreview/registry'

registerDocEntities([
  // ── Contract class ───────────────────────────────────────────────────
  {
    id: 'bp.contract',
    type: 'class',
    title: 'Contract',
    description:
      'First-class model↔world contract. Declares what data the outside world sees (Facets), named subsets (Projections), how data enters (Casts), integrity rules (Seals / Ward), and how validated data is written back (Imprint). Not a serializer — a typed framework primitive.',
    signature: 'class Contract:\n    class Spec:\n        model: type[Model]\n        projections: dict[str, list[str] | str]',
    language: 'python',
    example: {
      code: `from aquilia.contracts import Contract, TextFacet, IntFacet

class ProductContract(Contract):
    name = TextFacet(max_length=200)
    price = IntFacet(min_value=0)

    class Spec:
        model = Product
        projections = {
            "summary": ["id", "name", "price"],
            "detail": "__all__",
        }

# Outbound (model → dict):
bp = ProductContract(instance=product)
data = bp.data

# Inbound (dict → validated):
bp = ProductContract(data={"name": "Widget", "price": 9})
if bp.is_sealed():
    product = await bp.imprint()`,
      language: 'python',
    },
    related: [
      { label: 'Facets', href: '/docs/contracts/facets' },
      { label: 'Seals', href: '/docs/contracts/seals' },
      { label: 'Projections', href: '/docs/contracts/projections' },
      { label: 'Lenses', href: '/docs/contracts/lenses' },
    ],
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/contracts/overview',
    source: { file: 'aquilia/contracts/core.py', line: 89 },
  },

  // ── Spec inner class ─────────────────────────────────────────────────
  {
    id: 'bp.spec',
    type: 'class',
    title: 'Spec',
    description:
      'Inner class on a Contract (like Meta on a Model). Controls the model binding, field selection, projections, depth, validators, and strict mode. Parsed by ContractMeta into _SpecData.',
    signature: 'class Spec:\n    model: type[Model]\n    fields: list[str] | None\n    exclude: list[str] | None\n    projections: dict\n    depth: int = 3\n    strict: bool = False',
    language: 'python',
    parameters: [
      { name: 'model', type: 'type[Model]', description: 'The ORM model this contract contracts against.' },
      { name: 'fields', type: 'list[str] | None', optional: true, description: 'Explicit allowlist of fields. None = all.' },
      { name: 'exclude', type: 'list[str] | None', optional: true, description: 'Fields to exclude.' },
      { name: 'projections', type: 'dict', optional: true, description: 'Named field subsets. Use "__all__" to include all.' },
      { name: 'default_projection', type: 'str | None', optional: true, description: 'Projection used when none specified.' },
      { name: 'depth', type: 'int', optional: true, default: '3', description: 'Max nesting depth for related models.' },
      { name: 'strict', type: 'bool', optional: true, default: 'False', description: 'Reject unknown input fields as CastFault.' },
      { name: 'read_only_fields', type: 'tuple', optional: true, description: 'Fields ignored on inbound cast.' },
      { name: 'write_only_fields', type: 'tuple', optional: true, description: 'Fields excluded from outbound data.' },
    ],
    status: 'stable',
    docsHref: '/docs/contracts/overview',
    source: { file: 'aquilia/contracts/core.py', line: 160 },
  },

  // ── Facets ───────────────────────────────────────────────────────────
  {
    id: 'bp.facet',
    type: 'class',
    title: 'Facet',
    description:
      'Base descriptor for a single field on a Contract. Handles both outbound serialization (model value → wire value) and inbound casting (wire value → validated Python value). Subclasses: TextFacet, IntFacet, DateTimeFacet, ListFacet, etc.',
    signature: 'class Facet:\n    def __init__(self, *, required: bool = True, default=UNSET, null: bool = False, source: str | None = None, ...)',
    language: 'python',
    parameters: [
      { name: 'required', type: 'bool', optional: true, default: 'True', description: 'Fail CastFault if field missing on inbound.' },
      { name: 'default', optional: true, default: 'UNSET', description: 'Fallback when value is missing.' },
      { name: 'null', type: 'bool', optional: true, default: 'False', description: 'Allow None values.' },
      { name: 'source', type: 'str | None', optional: true, description: 'Read from a different attribute name on the model.' },
      { name: 'read_only', type: 'bool', optional: true, default: 'False', description: 'Exclude from inbound cast.' },
      { name: 'write_only', type: 'bool', optional: true, default: 'False', description: 'Exclude from outbound data.' },
      { name: 'validators', type: 'list', optional: true, description: 'Additional callable validators.' },
    ],
    related: [
      { label: 'TextFacet', id: 'bp.text_facet' },
      { label: 'IntFacet', id: 'bp.int_facet' },
      { label: 'Computed', id: 'bp.computed_facet' },
    ],
    status: 'stable',
    docsHref: '/docs/contracts/facets',
    source: { file: 'aquilia/contracts/facets.py' },
  },

  {
    id: 'bp.text_facet',
    type: 'class',
    title: 'TextFacet',
    description: 'Facet for string values. Validates max_length, min_length, and optional regex pattern.',
    signature: 'class TextFacet(Facet):\n    max_length: int | None\n    min_length: int | None\n    pattern: str | None\n    strip: bool = True',
    language: 'python',
    example: {
      code: `from aquilia.contracts import TextFacet

class UserContract(Contract):
    username = TextFacet(max_length=50, min_length=3, pattern=r"^[a-z0-9_]+$")
    bio = TextFacet(max_length=500, required=False, default="")`,
      language: 'python',
    },
    status: 'stable',
    docsHref: '/docs/contracts/facets',
    source: { file: 'aquilia/contracts/facets.py' },
  },

  {
    id: 'bp.int_facet',
    type: 'class',
    title: 'IntFacet',
    description: 'Facet for integer values. Validates min_value and max_value.',
    signature: 'class IntFacet(Facet):\n    min_value: int | None\n    max_value: int | None',
    language: 'python',
    example: { code: `price = IntFacet(min_value=0, max_value=99999)`, language: 'python' },
    status: 'stable',
    docsHref: '/docs/contracts/facets',
    source: { file: 'aquilia/contracts/facets.py' },
  },

  {
    id: 'bp.computed_facet',
    type: 'class',
    title: 'Computed',
    description: 'Facet that computes its value at serialization time by calling a method on the Contract instance. Always read-only.',
    signature: 'class Computed(Facet):\n    source: Callable',
    language: 'python',
    example: {
      code: `from aquilia.contracts import Contract, Computed

class OrderContract(Contract):
    total = Computed(lambda bp: sum(i.price * i.qty for i in bp.instance.items))

    class Spec:
        model = Order`,
      language: 'python',
    },
    notes: [{ kind: 'tip', text: 'You can also use the @computed decorator instead of Computed() directly.' }],
    status: 'stable',
    docsHref: '/docs/contracts/facets',
    source: { file: 'aquilia/contracts/facets.py' },
  },

  // ── @computed decorator ───────────────────────────────────────────────
  {
    id: 'bp.computed_decorator',
    type: 'decorator',
    title: '@computed',
    description: 'Marks a Contract method as a computed read-only facet. The method receives the Contract instance and should return the serialized value.',
    signature: '@computed\ndef field_name(self) -> Any: ...',
    language: 'python',
    example: {
      code: `from aquilia.contracts import Contract
from aquilia.contracts.annotations import computed

class OrderContract(Contract):
    @computed
    def item_count(self) -> int:
        return len(self.instance.items)

    class Spec:
        model = Order`,
      language: 'python',
    },
    status: 'stable',
    docsHref: '/docs/contracts/facets',
    source: { file: 'aquilia/contracts/annotations.py' },
  },

  // ── Lens ─────────────────────────────────────────────────────────────
  {
    id: 'bp.lens',
    type: 'class',
    title: 'Lens',
    description:
      'Transforms a value through a chain of operations during serialization or deserialization. Lenses compose: Lens("field").upper().strip().truncate(100). They are lazy — evaluated only when the Contract produces data.',
    signature: 'class Lens:\n    def __init__(self, source: str)\n    def upper(self) -> Lens\n    def lower(self) -> Lens\n    def strip(self) -> Lens\n    def truncate(self, n: int) -> Lens',
    language: 'python',
    example: {
      code: `from aquilia.contracts import Lens

class ArticleContract(Contract):
    # Render title as uppercase, trimmed slug
    slug = Lens("title").lower().strip().replace(" ", "-").truncate(50)
    excerpt = Lens("body").truncate(160).strip()

    class Spec:
        model = Article`,
      language: 'python',
    },
    related: [{ label: 'Projections', href: '/docs/contracts/projections' }],
    status: 'stable',
    docsHref: '/docs/contracts/lenses',
    source: { file: 'aquilia/contracts/lenses.py' },
  },

  // ── Ward / Seal ───────────────────────────────────────────────────────
  {
    id: 'bp.ward',
    type: 'decorator',
    title: '@ward',
    description:
      'Marks a Contract method as a validator (a "Ward"). Ward methods run after all individual Facet validations, allowing cross-field checks. Must return None or raise SealFault.',
    signature: '@ward\ndef validate_method(self) -> None: ...',
    language: 'python',
    example: {
      code: `from aquilia.contracts import Contract, SealFault
from aquilia.contracts.ward import ward

class EventContract(Contract):
    start_date = DateFacet()
    end_date = DateFacet()

    @ward
    def check_dates(self):
        if self.validated["end_date"] <= self.validated["start_date"]:
            raise SealFault({"end_date": "Must be after start_date"})

    class Spec:
        model = Event`,
      language: 'python',
    },
    related: [{ label: 'Contract.is_sealed()', id: 'bp.is_sealed' }, { label: 'SealFault', id: 'bp.seal_fault' }],
    status: 'stable',
    docsHref: '/docs/contracts/seals',
    source: { file: 'aquilia/contracts/ward.py' },
  },

  {
    id: 'bp.is_sealed',
    type: 'method',
    title: 'is_sealed()',
    description: 'Run all Facet validations and Ward methods. Returns True when all pass. Call before imprint(). Access errors via contract.errors.',
    signature: 'def is_sealed(self) -> bool',
    language: 'python',
    example: {
      code: `bp = UserContract(data=request.json)
if not bp.is_sealed():
    return Response.json({"errors": bp.errors}, status=422)
user = await bp.imprint()`,
      language: 'python',
    },
    related: [{ label: 'imprint()', id: 'bp.imprint' }, { label: '@ward', id: 'bp.ward' }],
    status: 'stable',
    docsHref: '/docs/contracts/seals',
    source: { file: 'aquilia/contracts/core.py' },
  },

  {
    id: 'bp.imprint',
    type: 'method',
    title: 'imprint()',
    description: 'Write validated data back to the model (create or update). Must call is_sealed() first. Returns the created/updated model instance.',
    signature: 'async def imprint(self, db: AquiliaDatabase | None = None, instance: Model | None = None) -> Model',
    language: 'python',
    example: {
      code: `bp = UserContract(data=request.json)
if bp.is_sealed():
    user = await bp.imprint(db=db)
    return Response.json({"id": user.id})`,
      language: 'python',
    },
    related: [{ label: 'is_sealed()', id: 'bp.is_sealed' }],
    status: 'stable',
    docsHref: '/docs/contracts/seals',
    source: { file: 'aquilia/contracts/core.py' },
  },

  // ── Projections ───────────────────────────────────────────────────────
  {
    id: 'bp.projection',
    type: 'type',
    title: 'Projection',
    description:
      'A named field subset declared in Spec.projections. Use "__all__" to include every facet, or a list of field names for a specific subset. Apply via contract["projection_name"] or ProjectionRegistry.',
    signature: 'projections: dict[str, list[str] | str]',
    language: 'python',
    example: {
      code: `class ProductContract(Contract):
    class Spec:
        model = Product
        projections = {
            "summary": ["id", "name", "price"],
            "admin":   ["id", "name", "price", "cost", "supplier"],
            "detail":  "__all__",
        }

# Apply at route:
@GET("/products", response_contract=ProductContract["summary"])
async def list_products(): ...`,
      language: 'python',
    },
    related: [{ label: 'Lens', id: 'bp.lens' }],
    status: 'stable',
    docsHref: '/docs/contracts/projections',
    source: { file: 'aquilia/contracts/projections.py' },
  },

  // ── Integration helpers ───────────────────────────────────────────────
  {
    id: 'bp.request_contract',
    type: 'decorator',
    title: 'request_contract',
    description: 'Route decorator argument that binds a Contract to request body parsing. The contract is cast from the request body and injected as a typed parameter into the controller method.',
    signature: '@POST("/users", request_contract=UserContract)',
    language: 'python',
    example: {
      code: `@POST("/users", request_contract=UserContract)
async def create_user(ctx: RequestCtx, contract: UserContract):
    if not contract.is_sealed():
        return Response.json(contract.errors, status=422)
    user = await contract.imprint(db=ctx.db)
    return Response.json(UserContract(instance=user).data, status=201)`,
      language: 'python',
    },
    related: [{ label: 'response_contract', id: 'bp.response_contract' }],
    status: 'stable',
    docsHref: '/docs/contracts/integration',
    source: { file: 'aquilia/contracts/integration.py' },
  },

  {
    id: 'bp.response_contract',
    type: 'decorator',
    title: 'response_contract',
    description: 'Route decorator argument that automatically serializes the return value through a Contract before sending the HTTP response.',
    signature: '@GET("/products", response_contract=ProductContract["summary"])',
    language: 'python',
    example: {
      code: `@GET("/products", response_contract=ProductContract["summary"])
async def list_products(ctx: RequestCtx):
    return await Product.objects.all()  # Aquilia serializes each item automatically`,
      language: 'python',
    },
    related: [{ label: 'request_contract', id: 'bp.request_contract' }],
    status: 'stable',
    docsHref: '/docs/contracts/integration',
    source: { file: 'aquilia/contracts/integration.py' },
  },

  // ── Faults ────────────────────────────────────────────────────────────
  {
    id: 'bp.seal_fault',
    type: 'class',
    title: 'SealFault',
    description: 'Raised when contract validation fails (a Ward rejects the data). Contains a dict of field-level error messages.',
    signature: 'class SealFault(ContractFault):\n    errors: dict[str, list[str]]',
    language: 'python',
    example: { code: `raise SealFault({"password": ["Too short (min 8 chars)"]})`, language: 'python' },
    status: 'stable',
    docsHref: '/docs/contracts/faults',
    source: { file: 'aquilia/contracts/exceptions.py' },
  },

  {
    id: 'bp.cast_fault',
    type: 'class',
    title: 'CastFault',
    description: 'Raised when inbound data cannot be coerced to the expected type by a Facet (e.g., "abc" for IntFacet).',
    signature: 'class CastFault(ContractFault):\n    field: str\n    value: Any\n    expected_type: str',
    language: 'python',
    status: 'stable',
    docsHref: '/docs/contracts/faults',
    source: { file: 'aquilia/contracts/exceptions.py' },
  },

  // ── Schema generation ─────────────────────────────────────────────────
  {
    id: 'bp.generate_schema',
    type: 'function',
    title: 'generate_schema()',
    description: 'Generate a JSON Schema (OpenAPI-compatible) dict from a Contract class. Used internally by the OpenAPI integration.',
    signature: 'def generate_schema(contract_cls: type[Contract]) -> dict',
    language: 'python',
    example: {
      code: `from aquilia.contracts import generate_schema

schema = generate_schema(UserContract)
# {"type": "object", "properties": {"name": {"type": "string"}, ...}}`,
      language: 'python',
    },
    related: [{ label: 'Schemas', href: '/docs/contracts/schemas' }],
    status: 'stable',
    docsHref: '/docs/contracts/schemas',
    source: { file: 'aquilia/contracts/schema.py' },
  },

  // ── Sigil ─────────────────────────────────────────────────────────────
  {
    id: 'bp.sigil',
    type: 'class',
    title: 'Sigil',
    description:
      'Advanced typed field specification system. FieldSpec instances declare full type contracts including nested types, union types, and constraints. The Sigil class compiles FieldSpec trees into validation pipelines.',
    signature: 'class Sigil:\n    def __init__(self, *specs: FieldSpec)',
    language: 'python',
    status: 'experimental',
    docsHref: '/docs/contracts/annotations',
    source: { file: 'aquilia/contracts/sigil.py' },
  },
])
