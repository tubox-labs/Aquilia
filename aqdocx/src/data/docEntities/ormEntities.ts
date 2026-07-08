import { registerDocEntities } from '../../lib/docPreview/registry'

registerDocEntities([
  // ── Core model class ─────────────────────────────────────────────────
  {
    id: 'orm.model',
    type: 'class',
    title: 'Model',
    description:
      'Base class for all Aquilia ORM models. Subclass it and declare field attributes. A ModelMeta metaclass collects fields, injects auto-PKs, parses the inner Meta class, registers the model globally, and attaches a default Manager.',
    signature: 'class Model:\n    table: str\n    objects: Manager\n    _meta: Options',
    language: 'python',
    parameters: [
      { name: 'table', type: 'str', optional: true, description: 'Explicit table name. Defaults to class name lower-cased.' },
    ],
    example: {
      code: `from aquilia.models import Model
from aquilia.models.fields_module import CharField, EmailField, BooleanField

class User(Model):
    table = "users"
    name = CharField(max_length=150)
    email = EmailField(unique=True)
    active = BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]`,
      language: 'python',
    },
    related: [
      { label: 'Manager', id: 'orm.manager' },
      { label: 'Fields', href: '/docs/models/fields' },
      { label: 'QuerySet', id: 'orm.queryset' },
      { label: 'Meta class', id: 'orm.meta' },
    ],
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/models/overview',
    source: { file: 'aquilia/models/base.py' },
  },

  // ── Instance methods ─────────────────────────────────────────────────
  {
    id: 'orm.model.save',
    type: 'method',
    title: 'save()',
    description:
      'Persist the instance. Issues INSERT when the instance has no PK set; UPDATE otherwise. Fires pre_save and post_save signals. Pass update_fields to limit which columns are written.',
    signature: 'async def save(self, db: AquiliaDatabase, update_fields: list[str] | None = None) -> None',
    language: 'python',
    parameters: [
      { name: 'db', type: 'AquiliaDatabase', description: 'Active database connection.' },
      { name: 'update_fields', type: 'list[str] | None', optional: true, default: 'None', description: 'Limit UPDATE to these columns only.' },
    ],
    example: {
      code: `user = User(name="Alice", email="alice@co.com")
await user.save(db)          # INSERT — assigns user.id

user.name = "Alice Smith"
await user.save(db, update_fields=["name"])   # UPDATE users SET name=? WHERE id=?`,
      language: 'python',
    },
    related: [{ label: 'delete_instance()', id: 'orm.model.delete_instance' }, { label: 'pre_save', id: 'orm.signal.pre_save' }],
    status: 'stable',
    docsHref: '/docs/models/overview',
    source: { file: 'aquilia/models/base.py' },
  },

  {
    id: 'orm.model.delete_instance',
    type: 'method',
    title: 'delete_instance()',
    description: 'DELETE this row from the database. Fires pre_delete and post_delete signals.',
    signature: 'async def delete_instance(self, db: AquiliaDatabase) -> None',
    language: 'python',
    parameters: [{ name: 'db', type: 'AquiliaDatabase', description: 'Active database connection.' }],
    example: { code: 'await user.delete_instance(db)', language: 'python' },
    related: [{ label: 'post_delete', id: 'orm.signal.post_delete' }],
    status: 'stable',
    docsHref: '/docs/models/overview',
    source: { file: 'aquilia/models/base.py' },
  },

  {
    id: 'orm.model.full_clean',
    type: 'method',
    title: 'full_clean()',
    description: 'Run all field-level validators. Raises ValidationError listing all failures. Call before save() to validate data from untrusted sources.',
    signature: 'def full_clean(self) -> None',
    language: 'python',
    example: {
      code: `user = User(name="", email="bad")
try:
    user.full_clean()
except ValidationError as e:
    print(e.errors)  # {"name": ["This field cannot be blank"], ...}`,
      language: 'python',
    },
    status: 'stable',
    docsHref: '/docs/models/overview',
    source: { file: 'aquilia/models/base.py' },
  },

  {
    id: 'orm.model.to_dict',
    type: 'method',
    title: 'to_dict()',
    description: 'Serialize the instance to a plain Python dict. Optionally filter to specific fields or exclude specific fields.',
    signature: 'def to_dict(self, fields: list[str] | None = None, exclude: list[str] | None = None) -> dict',
    language: 'python',
    parameters: [
      { name: 'fields', type: 'list[str] | None', optional: true, description: 'Allowlist of field names to include.' },
      { name: 'exclude', type: 'list[str] | None', optional: true, description: 'Fields to exclude from the result.' },
    ],
    example: {
      code: `user.to_dict()
# → {"id": 1, "name": "Alice", "email": "alice@co.com", ...}

user.to_dict(fields=["id", "name"])
# → {"id": 1, "name": "Alice"}`,
      language: 'python',
    },
    status: 'stable',
    docsHref: '/docs/models/overview',
    source: { file: 'aquilia/models/base.py' },
  },

  // ── Manager ──────────────────────────────────────────────────────────
  {
    id: 'orm.manager',
    type: 'class',
    title: 'Manager',
    description:
      'The objects-style query interface attached to every Model. Calling Model.objects returns a fresh QuerySet. The default manager is a Manager instance — you can subclass it to add custom query methods.',
    signature: 'class Manager:\n    def get_queryset(self) -> QuerySet: ...',
    language: 'python',
    example: {
      code: `# Default manager
users = await User.objects.filter(active=True).all()

# Custom manager
class PublishedManager(Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status="published")

class Article(Model):
    table = "articles"
    objects = PublishedManager()`,
      language: 'python',
    },
    related: [{ label: 'QuerySet', id: 'orm.queryset' }, { label: 'Model', id: 'orm.model' }],
    status: 'stable',
    docsHref: '/docs/models/queryset',
    source: { file: 'aquilia/models/manager.py' },
  },

  // ── QuerySet ─────────────────────────────────────────────────────────
  {
    id: 'orm.queryset',
    type: 'class',
    title: 'QuerySet',
    description:
      'Immutable, clone-on-write async query builder. Each chain method returns a new QuerySet — nothing hits the database until you call a terminal method (all, first, get, count, etc.).',
    signature: 'class QuerySet[M]:\n    def filter(**kwargs) -> QuerySet[M]\n    async def all() -> list[M]',
    language: 'python',
    example: {
      code: `qs = User.objects.filter(active=True).order("-created_at").limit(20)

# Terminal — hits DB:
users = await qs.all()
count = await qs.count()
first = await qs.first()   # None if empty
one   = await qs.get(id=5) # raises if not found`,
      language: 'python',
    },
    related: [
      { label: 'filter()', id: 'orm.queryset.filter' },
      { label: 'Q objects', id: 'orm.q' },
      { label: 'Manager', id: 'orm.manager' },
    ],
    status: 'stable',
    docsHref: '/docs/models/queryset',
    source: { file: 'aquilia/models/query.py' },
  },

  {
    id: 'orm.queryset.filter',
    type: 'method',
    title: 'filter()',
    description:
      'Narrow the QuerySet by field lookups. Supports Django-style double-underscore lookups: exact, iexact, contains, icontains, startswith, endswith, in, gt, gte, lt, lte, range, isnull, regex.',
    signature: 'def filter(self, *q: Q, **kwargs) -> QuerySet',
    language: 'python',
    parameters: [
      { name: '*q', type: 'Q', optional: true, description: 'Q objects for complex OR/AND logic.' },
      { name: '**kwargs', description: 'Field lookup expressions (field__lookup=value).' },
    ],
    example: {
      code: `# Simple exact match
User.objects.filter(active=True)

# Double-underscore lookup
User.objects.filter(name__icontains="alice")
User.objects.filter(created_at__gte=cutoff)
User.objects.filter(id__in=[1, 2, 3])

# Q objects for OR
from aquilia.models import Q
User.objects.filter(Q(name="Alice") | Q(name="Bob"))`,
      language: 'python',
    },
    related: [{ label: 'exclude()', id: 'orm.queryset.exclude' }, { label: 'Q objects', id: 'orm.q' }],
    status: 'stable',
    docsHref: '/docs/models/queryset',
    source: { file: 'aquilia/models/query.py' },
  },

  {
    id: 'orm.queryset.exclude',
    type: 'method',
    title: 'exclude()',
    description: 'Exclude rows matching the given lookups. Equivalent to WHERE NOT (...).',
    signature: 'def exclude(self, *q: Q, **kwargs) -> QuerySet',
    language: 'python',
    example: { code: 'User.objects.exclude(active=False)', language: 'python' },
    status: 'stable',
    docsHref: '/docs/models/queryset',
    source: { file: 'aquilia/models/query.py' },
  },

  {
    id: 'orm.queryset.select_related',
    type: 'method',
    title: 'select_related()',
    description: 'Fetch ForeignKey / OneToOne related objects via a single JOIN query. Eliminates N+1 for to-one relations.',
    signature: 'def select_related(self, *fields: str) -> QuerySet',
    language: 'python',
    example: {
      code: `# Loads post.author in the same SQL JOIN
posts = await Post.objects.select_related("author").all()
for post in posts:
    print(post.author.name)  # no extra query`,
      language: 'python',
    },
    related: [{ label: 'prefetch_related()', id: 'orm.queryset.prefetch_related' }],
    status: 'stable',
    docsHref: '/docs/models/relationships',
    source: { file: 'aquilia/models/query.py' },
  },

  {
    id: 'orm.queryset.prefetch_related',
    type: 'method',
    title: 'prefetch_related()',
    description: 'Fetch ManyToMany or reverse-FK relations in a separate query per relation and stitch results in Python. Use Prefetch() to customize the nested QuerySet.',
    signature: 'def prefetch_related(self, *lookups: str | Prefetch) -> QuerySet',
    language: 'python',
    example: {
      code: `from aquilia.models import Prefetch

posts = await Post.objects.prefetch_related(
    Prefetch("tags", queryset=Tag.objects.filter(active=True))
).all()`,
      language: 'python',
    },
    related: [{ label: 'select_related()', id: 'orm.queryset.select_related' }],
    status: 'stable',
    docsHref: '/docs/models/relationships',
    source: { file: 'aquilia/models/query.py' },
  },

  {
    id: 'orm.queryset.annotate',
    type: 'method',
    title: 'annotate()',
    description: 'Add computed columns to each row using aggregate or expression objects (Count, Sum, F, Case, Subquery…).',
    signature: 'def annotate(self, **expressions) -> QuerySet',
    language: 'python',
    example: {
      code: `from aquilia.models import Count, F

users = await User.objects.annotate(
    post_count=Count("posts"),
    name_upper=F("name").upper(),
).all()`,
      language: 'python',
    },
    related: [{ label: 'Aggregation', href: '/docs/models/aggregation' }],
    status: 'stable',
    docsHref: '/docs/models/aggregation',
    source: { file: 'aquilia/models/query.py' },
  },

  // ── Q object ─────────────────────────────────────────────────────────
  {
    id: 'orm.q',
    type: 'class',
    title: 'Q',
    description: 'Encapsulates a single filter expression. Supports & (AND), | (OR), and ~ (NOT) operators to build compound WHERE clauses.',
    signature: 'class Q:\n    def __init__(self, **kwargs)\n    def __and__(self, other: Q) -> Q\n    def __or__(self, other: Q) -> Q\n    def __invert__(self) -> Q',
    language: 'python',
    example: {
      code: `from aquilia.models import Q

# (active=True AND role="admin") OR email ends with "@co.com"
qs = User.objects.filter(
    (Q(active=True) & Q(role="admin")) | Q(email__endswith="@co.com")
)

# NOT active
qs = User.objects.filter(~Q(active=True))`,
      language: 'python',
    },
    related: [{ label: 'filter()', id: 'orm.queryset.filter' }],
    status: 'stable',
    docsHref: '/docs/models/queryset',
    source: { file: 'aquilia/models/query.py' },
  },

  // ── F expression ─────────────────────────────────────────────────────
  {
    id: 'orm.f',
    type: 'class',
    title: 'F',
    description: 'References a model field in a database expression. Allows arithmetic, string ops, and comparisons directly in SQL without pulling data into Python.',
    signature: 'class F:\n    def __init__(self, name: str)',
    language: 'python',
    example: {
      code: `from aquilia.models import F

# Increment views without a Python read-modify-write
await Post.objects.filter(id=42).update(views=F("views") + 1)

# Filter by computed comparison
posts = await Post.objects.filter(views__gt=F("likes") * 2).all()`,
      language: 'python',
    },
    status: 'stable',
    docsHref: '/docs/models/queryset',
    source: { file: 'aquilia/models/expression.py' },
  },

  // ── atomic ───────────────────────────────────────────────────────────
  {
    id: 'orm.atomic',
    type: 'function',
    title: 'atomic()',
    description:
      'Async context manager that wraps a block in a database transaction. Nested calls create SAVEPOINTs. Rolls back automatically on exception.',
    signature: '@asynccontextmanager\nasync def atomic(db: AquiliaDatabase, isolation: str | None = None) -> AsyncIterator[None]',
    language: 'python',
    parameters: [
      { name: 'db', type: 'AquiliaDatabase', description: 'Database to run the transaction on.' },
      { name: 'isolation', type: 'str | None', optional: true, description: 'Isolation level: READ COMMITTED, REPEATABLE READ, SERIALIZABLE.' },
    ],
    example: {
      code: `from aquilia.models import atomic

async with atomic(db):
    user = await User.objects.create(db, name="Alice", email="a@co.com")
    await Profile.objects.create(db, user_id=user.id, bio="Hello")
    # Both committed, or both rolled back`,
      language: 'python',
    },
    related: [{ label: 'Transactions', href: '/docs/models/transactions' }],
    status: 'stable',
    docsHref: '/docs/models/transactions',
    source: { file: 'aquilia/models/transactions.py' },
  },

  // ── Signals ─────────────────────────────────────────────────────────
  {
    id: 'orm.signal.pre_save',
    type: 'event',
    title: 'pre_save',
    description: 'Fired before Model.save() executes SQL. Receives the instance and a created flag.',
    signature: 'pre_save.connect(receiver, sender=MyModel)',
    language: 'python',
    example: {
      code: `from aquilia.models import pre_save, receiver

@receiver(pre_save, sender=User)
async def hash_password(sender, instance, created, **kwargs):
    if created or instance._password_changed:
        instance.password = hash(instance.password)`,
      language: 'python',
    },
    related: [{ label: 'post_save', id: 'orm.signal.post_save' }, { label: 'Signals', href: '/docs/models/signals' }],
    status: 'stable',
    docsHref: '/docs/models/signals',
    source: { file: 'aquilia/models/signals.py' },
  },

  {
    id: 'orm.signal.post_save',
    type: 'event',
    title: 'post_save',
    description: 'Fired after Model.save() commits. Receives instance, created flag, and update_fields.',
    signature: 'post_save.connect(receiver, sender=MyModel)',
    language: 'python',
    example: {
      code: `@receiver(post_save, sender=Order)
async def notify_fulfillment(sender, instance, created, **kwargs):
    if created:
        await queue.enqueue("send_confirmation", order_id=instance.id)`,
      language: 'python',
    },
    related: [{ label: 'pre_save', id: 'orm.signal.pre_save' }],
    status: 'stable',
    docsHref: '/docs/models/signals',
    source: { file: 'aquilia/models/signals.py' },
  },

  {
    id: 'orm.signal.post_delete',
    type: 'event',
    title: 'post_delete',
    description: 'Fired after delete_instance() removes a row. Receives the deleted instance.',
    signature: 'post_delete.connect(receiver, sender=MyModel)',
    language: 'python',
    example: {
      code: `@receiver(post_delete, sender=User)
async def cleanup_sessions(sender, instance, **kwargs):
    await Session.objects.filter(user_id=instance.id).delete()`,
      language: 'python',
    },
    status: 'stable',
    docsHref: '/docs/models/signals',
    source: { file: 'aquilia/models/signals.py' },
  },

  // ── Meta ─────────────────────────────────────────────────────────────
  {
    id: 'orm.meta',
    type: 'class',
    title: 'Meta',
    description:
      'Inner class on a Model that controls table-level options: default ordering, indexes, constraints, abstract flag, custom table name, unique_together, and more. Parsed by ModelMeta into an Options instance stored as Model._meta.',
    signature: 'class Meta:\n    ordering: list[str]\n    indexes: list[Index]\n    abstract: bool\n    db_table: str',
    language: 'python',
    example: {
      code: `class Article(Model):
    table = "articles"
    title = CharField(max_length=200)

    class Meta:
        ordering = ["-published_at"]
        abstract = False
        indexes = [Index(fields=["title"])]
        constraints = [UniqueConstraint(fields=["title"], name="uq_title")]`,
      language: 'python',
    },
    related: [{ label: 'Model', id: 'orm.model' }],
    status: 'stable',
    docsHref: '/docs/models/overview',
    source: { file: 'aquilia/models/options.py' },
  },

  // ── Migration DSL ────────────────────────────────────────────────────
  {
    id: 'orm.migration',
    type: 'class',
    title: 'Migration',
    description:
      'A single versioned schema change. Declare dependencies and a list of DSL Operations. The runner applies them in dependency order with automatic rollback on failure.',
    signature: 'class Migration:\n    dependencies: list[str]\n    operations: list[Operation]',
    language: 'python',
    example: {
      code: `from aquilia.models import Migration, DSLCreateModel, DSLAddField, ColumnDef as C

class Migration_0001(Migration):
    dependencies = []
    operations = [
        DSLCreateModel("users", columns=[
            C.int("id", primary_key=True),
            C.text("email", unique=True),
            C.bool("active", default=True),
        ]),
    ]`,
      language: 'python',
    },
    related: [{ label: 'Migrations', href: '/docs/models/migrations' }],
    status: 'stable',
    docsHref: '/docs/models/migrations',
    source: { file: 'aquilia/models/migration_dsl.py' },
  },

  // ── Aggregates ───────────────────────────────────────────────────────
  {
    id: 'orm.count',
    type: 'function',
    title: 'Count()',
    description: 'Aggregate: COUNT(field). Use with annotate() or pass to aggregate().',
    signature: 'Count(field: str, distinct: bool = False) -> Aggregate',
    language: 'python',
    example: {
      code: `from aquilia.models import Count

result = await User.objects.aggregate(total=Count("id"))
# → {"total": 42}

# Per-user post count
users = await User.objects.annotate(posts=Count("post")).all()`,
      language: 'python',
    },
    related: [{ label: 'Sum()', id: 'orm.sum' }, { label: 'Aggregation', href: '/docs/models/aggregation' }],
    status: 'stable',
    docsHref: '/docs/models/aggregation',
    source: { file: 'aquilia/models/aggregate.py' },
  },

  {
    id: 'orm.sum',
    type: 'function',
    title: 'Sum()',
    description: 'Aggregate: SUM(field).',
    signature: 'Sum(field: str) -> Aggregate',
    language: 'python',
    example: { code: `result = await Order.objects.aggregate(revenue=Sum("total"))`, language: 'python' },
    related: [{ label: 'Count()', id: 'orm.count' }, { label: 'Avg()', id: 'orm.avg' }],
    status: 'stable',
    docsHref: '/docs/models/aggregation',
    source: { file: 'aquilia/models/aggregate.py' },
  },

  {
    id: 'orm.avg',
    type: 'function',
    title: 'Avg()',
    description: 'Aggregate: AVG(field).',
    signature: 'Avg(field: str) -> Aggregate',
    language: 'python',
    example: { code: `result = await Product.objects.aggregate(avg_price=Avg("price"))`, language: 'python' },
    status: 'stable',
    docsHref: '/docs/models/aggregation',
    source: { file: 'aquilia/models/aggregate.py' },
  },

  // ── ModelRegistry ────────────────────────────────────────────────────
  {
    id: 'orm.registry',
    type: 'class',
    title: 'ModelRegistry',
    description:
      'Global registry where every Model class is automatically registered by the ModelMeta metaclass. Resolves forward references, handles topological ordering for CREATE TABLE, and provides runtime lookups by name.',
    signature: 'class ModelRegistry:\n    @staticmethod\n    def get(name: str) -> type[Model]\n    @staticmethod\n    async def create_tables(db) -> None',
    language: 'python',
    example: {
      code: `from aquilia.models.registry import ModelRegistry

UserModel = ModelRegistry.get("User")
await ModelRegistry.create_tables(db)   # respects FK ordering`,
      language: 'python',
    },
    status: 'stable',
    docsHref: '/docs/models/advanced',
    source: { file: 'aquilia/models/registry.py' },
  },
])
