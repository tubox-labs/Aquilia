import { registerDocEntities } from '../../lib/docPreview/registry'

registerDocEntities([
  {
    id: 'vectordb.VectorModel',
    type: 'class',
    title: 'VectorModel',
    description:
      'Declarative base for a vector-searchable record. Field roles come from Annotated metadata or unified field objects, and Meta names the collection and store alias. The metaclass resolves every attribute to exactly one slot at class creation, so nothing is introspected on the query path.',
    signature:
      'class VectorModel:\n    class Meta:\n        collection: str\n        store: str = "default"\n        dimension: int | None = None\n\n    vectors: VectorManager   # attached by the metaclass\n\n    async def save(self, *, embed: bool | None = None) -> Self\n    async def refresh(self) -> Self\n    async def delete_instance(self) -> bool\n    def validate(self) -> None',
    language: 'python',
    example: {
      code: `from aquilia.vectordb import VectorModel, KeyField, TextField, VectorField, Field

class Document(VectorModel):
    key:    str         = KeyField(prefix="doc_")
    body:   str         = TextField(embed=True, min_length=1)
    vector: list[float] = VectorField(dimension=384)
    source: str         = Field(default="web")

    class Meta:
        collection = "documents"
        store = "default"`,
      language: 'python',
    },
    status: 'beta',
    version: 'v1.4.0b3+',
    docsHref: '/docs/vectordb/models',
  },
  {
    id: 'vectordb.VectorField',
    type: 'class',
    title: 'VectorField',
    description:
      'Marks the attribute holding the raw vector and declares its length. At most one per model — elips holds dimension and metric database-global, so every model sharing a store must agree on both. Equivalent to the Annotated marker Dimension(n).',
    signature: 'VectorField(dimension: int, *, metric: str | None = None, index: str | None = None)',
    language: 'python',
    status: 'beta',
    version: 'v1.4.0b3+',
    docsHref: '/docs/vectordb/models',
  },
  {
    id: 'vectordb.VectorManager',
    type: 'class',
    title: 'VectorManager',
    description:
      'Attached to every concrete model as Model.vectors. Entry point for searching, reading by key, writing and maintenance. Shorthand methods delegate to a fresh VectorQuery.',
    signature:
      'class VectorManager:\n    def query(self) -> VectorQuery\n    def filter(self, *nodes, **lookups) -> VectorQuery\n    def exclude(self, *nodes, **lookups) -> VectorQuery\n    async def search(self, text=None, *, vector=None, limit=10, **lookups) -> list[Hit]\n    async def get(self, key: str) -> Model | None\n    async def get_many(self, keys: list[str]) -> list[Model]\n    async def add(self, instance, *, embed=None) -> Model\n    async def remove(self, key: str) -> bool\n    async def count(self) -> int\n    async def health(self) -> dict',
    language: 'python',
    example: {
      code: `hits = await Document.vectors.search("release notes", limit=10)
doc  = await Document.vectors.get("doc:1")
n    = await Document.vectors.count()`,
      language: 'python',
    },
    status: 'beta',
    version: 'v1.4.0b3+',
    docsHref: '/docs/vectordb/queries',
  },
  {
    id: 'vectordb.VectorQuery',
    type: 'class',
    title: 'VectorQuery',
    description:
      'Lazy, chainable query over a collection. Every builder method clones rather than mutating, so a base query can be shared and specialised safely. Nothing touches the store until a terminal is awaited.',
    signature:
      'class VectorQuery:\n    def filter(self, *nodes, **lookups) -> Self\n    def exclude(self, *nodes, **lookups) -> Self\n    def limit(self, n: int | None) -> Self\n    def top(self, n: int) -> Self          # alias of limit(), for search mode\n    def offset(self, n: int) -> Self       # scan mode only\n    def min_score(self, score: float) -> Self\n    async def search(self, text=None, *, vector=None, limit=None) -> list[Hit]\n    async def all(self) -> list[Model]\n    async def count(self) -> int\n    async def exists(self) -> bool\n    async def delete(self) -> int          # refused when unfiltered\n    async def explain(self, *, vector=None) -> dict',
    language: 'python',
    example: {
      code: `hits = await (
    Document.vectors.query()
    .filter(source="docs")
    .min_score(0.75)
    .top(10)
    .search("how do migrations work")
)`,
      language: 'python',
    },
    status: 'beta',
    version: 'v1.4.0b3+',
    docsHref: '/docs/vectordb/queries',
  },
  {
    id: 'vectordb.VF',
    type: 'class',
    title: 'VF',
    description:
      'Composable filter node — the OR / NOT companion to keyword lookups, which filter() only ANDs. Takes the same lookups and combines with & | ~. Named VF rather than Q to stay unmistakable against the SQL ORM\'s Q.',
    signature: 'VF(**lookups: Any)   # combine with & | ~',
    language: 'python',
    example: {
      code: `from aquilia.vectordb import VF

await Document.vectors.query().filter(
    (VF(kind="doc") | VF(kind="faq")) & VF(views__gte=10),
    ~VF(archived=True),
).all()`,
      language: 'python',
    },
    status: 'beta',
    version: 'v1.4.0b3+',
    docsHref: '/docs/vectordb/queries',
  },
  {
    id: 'vectordb.Hit',
    type: 'class',
    title: 'Hit',
    description:
      'One similarity-search result. Proxies attribute access to the underlying record, so hit.title works. score is normalised so higher always means more similar; distance is the raw value elips reported, where lower is closer.',
    signature:
      'class Hit:\n    record: VectorModel\n    score: float\n    distance: float\n    approximate: bool = False\n    codec: str = "none"',
    language: 'python',
    example: {
      code: `for hit in await Document.vectors.search("alpha", limit=5):
    if hit.approximate:
        # distance came from a reconstructed vector — the score is an estimate
        print(hit.codec)
    print(hit.score, hit.body)`,
      language: 'python',
    },
    status: 'beta',
    version: 'v1.4.0b3+',
    docsHref: '/docs/vectordb/queries',
  },
  {
    id: 'vectordb.integration',
    type: 'class',
    title: 'VectorDatabaseIntegration',
    description:
      "Workspace integration declaring the elips-backed stores opened at boot. stores maps an alias to that store's settings; outer dimension/metric/index/gpu/embedder values act as defaults a store may override. path is a local directory prefix, not a URL.",
    signature:
      'class VectorDatabaseIntegration:\n    path: str = "./.aquilia/vectors"\n    stores: dict[str, Any] | None = None\n    default: str = "default"\n    dimension: int | None = None\n    metric: str | None = None\n    index: str | None = None\n    gpu: Any | None = None\n    embedder: Any | None = None\n    auto_create: bool = True\n    read_only: bool = False\n    pool_threads: int = 4\n    enabled: bool = True',
    language: 'python',
    example: {
      code: `workspace.vectordb(
    path="./.aquilia/vectors",
    stores={"default": {"dimension": 384, "metric": "cosine"}},
)`,
      language: 'python',
    },
    status: 'beta',
    version: 'v1.4.0b3+',
    docsHref: '/docs/config/integrations',
  },
])
