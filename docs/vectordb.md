# Aquilia Vector Database

`aquilia.vectordb` is a typed model layer over [elips](https://pypi.org/project/elips/), an embedded vector database. It gives vector collections the same declarative shape Aquilia's SQL ORM gives tables — models, managers, queries, faults, subsystem lifecycle — without pretending the two storage engines are the same thing.

`elips` is an **optional dependency**. Importing `aquilia.vectordb` on an install without it succeeds; the fault surfaces at first *use*, as `VectorNotInstalledFault` carrying the install hint.

```bash
pip install 'aquilia[vectordb]'
```

---

## 1. Declaring a model

Vector models support **two interchangeable declaration styles**. Both compile to the same schema, so a codebase may use either — or mix them across models.

### Style 1 — unified fields (recommended)

One field object carries slot routing, defaults, storage aliasing, and every validation constraint:

```python
from datetime import datetime
from aquilia.vectordb import (
    VectorModel, Field, KeyField, VectorField, TextField, ScoreField, LinkField,
)

class Document(VectorModel):
    key:        str          = KeyField(prefix="doc_")
    body:       str          = TextField(embed=True, min_length=1, max_length=8192)
    vector:     list[float]  = VectorField(dimension=384)
    source:     str          = Field(default="web", indexed=True, max_length=256)
    views:      int          = Field(default=0, ge=0)
    score:      float | None = ScoreField()
    author_id:  int          = LinkField(User, on_delete="detach")
    created_at: datetime     = Field(default_factory=datetime.utcnow)

    class Meta:
        collection = "documents"
        store = "default"
        dimension = 384
```

### Style 2 — PEP 593 `Annotated`

```python
from typing import Annotated
from aquilia.vectordb import VectorModel, Field, KeyField, VectorField, TextField

class Document(VectorModel):
    key:    Annotated[str, KeyField(prefix="doc_")]
    body:   Annotated[str, TextField(embed=True, min_length=1)]
    vector: Annotated[list[float], VectorField(dimension=384)]
    source: Annotated[str, Field(indexed=True, max_length=256)] = "web"
    views:  Annotated[int, Field(ge=0, le=150)] = 0

    class Meta:
        collection = "documents"
```

Declaring a field in *both* places for one attribute raises `VectorSchemaFault`: there is no principled winner, so the contradiction is rejected rather than resolved by precedence.

In both styles a type checker sees `doc.source` as `str` and `doc.score` as `float | None`. Class access returns the *field* (so `Document.views >= 10` builds a filter), instance access returns the *value*.

### The field hierarchy

```
                        BaseVectorField
                               │
       ┌───────────────┬───────┴───────┬───────────────┐
   KeyField       VectorField      TextField      PayloadField (Field)
       │                                               │
   ScoreField                                      LinkField
```

| Field | Slot | Cardinality | Notes |
|---|---|---|---|
| `KeyField(prefix=…, autogenerate=…)` | Record key | Exactly one | `autogenerate=False` makes an unkeyed save a validation error |
| `VectorField(dimension=…, metric=…, index=…)` | The vector | At most one | |
| `TextField(embed=…, embedder=…, chunk_size=…, chunker=…)` | Source text | At most one | Also stored as a retrievable payload |
| `Field(...)` / `PayloadField(...)` | Metadata entry | Any number | Aliased as `Field` |
| `ScoreField()` | Similarity score | At most one | Read-only; never written |
| `LinkField(Model, on_delete=…)` | Metadata entry | Any number | A payload plus link metadata |

`ScoreField` is output only: populated by `search()`, `None` on a record fetched by key.

### Constraints

Constraints go directly on the field:

```python
source: str   = Field(indexed=True, min_length=1, max_length=256, pattern=r"^[a-z-]+$")
views:  int   = Field(default=0, ge=0, le=1_000_000)
ratio:  float = Field(gt=0.0, lt=1.0, multiple_of=0.05)
state:  str   = Field(choices=("draft", "live"))
label:  str   = Field(strip_whitespace=True, min_length=1)
```

**Numeric**: `ge`, `gt`, `le`, `lt`, `multiple_of`. **String**: `min_length`, `max_length`, `pattern`, `choices`, `strip_whitespace`.

`ge`/`le` are inclusive, `gt`/`lt` exclusive. `multiple_of` compares in `Decimal`, so `0.3` is a valid multiple of `0.1` despite binary float error. `strip_whitespace` normalizes *before* validation, so a value that would only pass `min_length` on trailing spaces does not pass.

Reusable bundles keep repeated rules in one place:

```python
from aquilia.vectordb import StringConstraints, NumericConstraints

SLUG = StringConstraints(min_length=1, max_length=64, pattern=r"^[a-z0-9-]+$")

class Article(VectorModel):
    slug: str = Field(constraints=SLUG)
    # A keyword narrows the bundle rather than being overridden by it:
    code: str = Field(constraints=SLUG, max_length=16)
```

`validate()` collects **every** failure before raising:

```python
try:
    doc.validate()
except VectorValidationFault as exc:
    print(exc.errors)   # {"body": "...", "views": "..."}
```

### Legacy `Annotated` markers

The original marker syntax (`Key()`, `Dimension(n)`, `Text()`, `Payload()`, `Score()`, plus `MinLength`/`MaxValue`/`Range`/…) is still fully supported and unchanged:

```python
from aquilia.vectordb import Key, Dimension, Text, Payload, MinLength

class Legacy(VectorModel):
    key:       Annotated[str, Key()]
    embedding: Annotated[list[float], Dimension(384)]
    body:      Annotated[str, Text(), MinLength(1)]
    source:    Annotated[str, Payload(indexed=True)]
```

New code should prefer the unified fields; existing models need no change.

### Inference

An attribute with neither a field nor a marker is routed by type:

1. `list[float]` / `Sequence[float]` → the vector slot.
2. `str` named `key` or `id` → the key slot.
3. Anything with a codec (§3) → a payload.
4. Anything else → `VectorSchemaFault` **at class creation**.

Text is never inferred. Text ingestion changes the write path and depends on a configured embedder; making that implicit would be a trap.

---


## 2. Configuration

Stores are declared in `workspace.py`. A store maps 1:1 to an elips database directory.

```python
from aquilia.workspace import Workspace
from aquilia.vectordb import GpuOptions, EmbedderOptions

workspace = (
    Workspace("myapp")
    .vectordb(
        path="./.aquilia/vectors",
        stores={
            "default": {
                "dimension": 384,
                "metric": "cosine",
                "index": "hnsw",
                "embedder": EmbedderOptions(provider="local", model="minilm-l6-v2"),
            },
            "images": {"dimension": 512, "metric": "l2"},
        },
        gpu=GpuOptions(policy="prefer_gpu", fallback="warn"),
    )
)
```

| Key | Default | Notes |
|---|---|---|
| `dimension` | `768` | Vector length. **Database-global** in elips. |
| `metric` | `"cosine"` | `cosine` \| `l2` \| `dot`. Also database-global. |
| `index` | `"flat"` | `flat` (exact) \| `hnsw` \| `ivf` (approximate). |
| `create_if_missing` | `True` | Set `False` in production so a missing store is a boot failure, not a silently empty one. |
| `read_only` | `False` | Opens without the writer lock; several processes may share one store for search. |
| `pool_threads` | `4` | See §9. |
| `embedder` | `None` | `EmbedderOptions` — see §6. |
| `quantization` | `None` | `QuantizationConfig` — see §9. |
| `chunking` | `None` | Store-level chunk defaults — see §7. |

Configuration may equivalently live in `aquilia.config.py` as a nested class, which the loader merges with the workspace block:

```python
class AquilaConfig:
    class VectorDB:
        enabled = True
        path = "./.aquilia/vectors"
        dimension = 384
        metric = "cosine"
        stores = {"default": {"dimension": 384}}
```

`dimension` and `metric` are held **database-global** by elips. Two models bound to one store must agree on both; a disagreement is a `VectorSchemaFault` at bind time rather than a silent coercion that would rank results by the wrong distance.

Models are discovered from `modules/<app>/vector_models.py` or a `vector_models/` package, or declared explicitly:

```python
# modules/blog/manifest.py
manifest = AppManifest(
    name="blog",
    version="1.0.0",
    vector_models=["modules.blog.vector_models"],
)
```

---

## 3. Payload codecs

elips metadata is flat and narrow: `MetaValue = bool | int | float | str`, one level deep, no lists. Richer types are routed through a codec.

| Python type | Stored as | Range-filterable |
|---|---|---|
| `bool` `int` `float` `str` | native | yes |
| `datetime` | POSIX timestamp (`float`) | **yes** |
| `date` `time` | ISO-8601 string | yes |
| `Decimal` | exact string | **no** |
| `UUID` | canonical string | no |
| `bytes` | base64 | no |
| `Enum` | member `.value` | follows the value type |
| `dict` `list` | — | **rejected at class creation** |

Two deliberate rejections, both because a silently wrong answer is worse than a loud failure:

- **Range filters over `Decimal`/`UUID`/`bytes`** raise `VectorLookupFault`. These encode to strings where lexicographic order is not value order (`"9" > "10"`). Equality and `__in` still work.
- **Nested `dict`/`list` payloads** raise `VectorSchemaFault` at class creation, not on first write — a store half-populated with unreadable values is much harder to recover from than an import error.

`datetime` encodes to an epoch float specifically so that ordering survives and `created__gte=...` works. Naive values are assumed UTC; decoding returns an aware UTC `datetime`, so the instant survives but the original `tzinfo` does not.

---

## 4. Reading and writing

```python
doc = Document(embedding=[...], body="release notes", source="docs", views=0)
await doc.save()          # key assigned if absent
await doc.refresh()       # reload from storage
await doc.delete_instance()
```

`save()` on a record with no key assigns a UUID. elips parses record keys as UUIDs, so a natural key like `"post:42"` is folded to a deterministic UUIDv5 — the same input always yields the same record, which is what makes re-saving overwrite rather than duplicate.

### Queries

`VectorQuery` mirrors the SQL `Q`: chainable methods clone, `async` terminals execute.

```python
hits = await Document.vectors.query().filter(source="docs").search(vector=q, limit=10)

for hit in hits:
    print(hit.score, hit.body)     # Hit proxies attribute access to the record
    print(hit.distance)            # raw elips distance, unconverted
```

Two query **modes**, and the difference is load-bearing:

- **Search mode** (`search(...)`) — results ordered by similarity; `limit` is the top-k handed to the index.
- **Scan mode** (`all()`, `count()`) — metadata filters only, results in *insertion* order. There is no query vector, so there is nothing to rank by. `order_by` is not offered rather than silently ignored.

`offset()` is rejected on `search()`: a similarity index returns top-k, so paging by offset would re-rank between pages.

### Lookups

| Lookup | Meaning |
|---|---|
| `field=v`, `field__exact` | equality |
| `field__ne` | inequality |
| `field__gt` `__gte` `__lt` `__lte` | range |
| `field__in=[...]` | membership |
| `field__range=(lo, hi)` | inclusive range |
| `field__contains` `__icontains` | substring |
| `field__startswith` `__endswith` | anchored match |
| `field__isnull` | **rejected** — see below |

The **key attribute** and `lineage__provider` / `lineage__model` / `lineage__revision` accept the same lookups. Both live outside the metadata namespace elips predicates reach, so they are evaluated in Python against hydrated records — correct, but they scan rather than narrow the index.

`__isnull` raises `VectorLookupFault`. elips has no null concept — an absent metadata key simply fails to match any predicate — so neither `True` nor `False` has a faithful translation. Model absence explicitly with a sentinel value or a boolean flag.

### Three filter syntaxes

All three compile to the same `CompiledFilter`, so they mix freely in one `filter()` call.

**Keyword lookups** — AND-ed:

```python
await Document.vectors.query().filter(source="docs", views__gte=10).all()
```

**`VF` trees** — for OR / NOT:

```python
from aquilia.vectordb import VF

await Document.vectors.query().filter(VF(source="docs") | VF(source="blog")).all()
await Document.vectors.query().exclude(views=0).all()
```

**Field expressions** — operator overloading on the field itself:

```python
await Document.vectors.query().filter(
    (Document.source == "docs") & (Document.views >= 10)
).all()

await Document.vectors.query().filter(
    Document.source.in_(["docs", "blog"]) | ~(Document.views == 0)
).all()

await Document.vectors.query().filter(
    Document.source.startswith("doc") & Document.views.between(1, 100)
).all()
```

`==` `!=` `>` `>=` `<` `<=` map to their lookups. Everything Python cannot overload is a named method: `.in_()`, `.contains()`, `.icontains()`, `.startswith()`, `.endswith()`, `.between()`. Combine with `&` `|` `~`.

Expressions are checked at build time: `Document.missing` raises `AttributeError`, and a `>` on a non-orderable payload raises `VectorLookupFault` where the comparison is written rather than at execution.

### EQL — string queries

For query text arriving from a config file, an admin UI, or an HTTP parameter:

```python
from aquilia.vectordb import parse_eql

node = parse_eql("source = 'docs' AND views >= 10 AND NOT archived = true")
await Document.vectors.query().filter(node).all()

# Or inline:
await Document.vectors.query().filter_eql("kind IN ('post','page') OR pinned = true").all()
```

Grammar: `AND` `OR` `NOT`, parentheses, `=` `!=` `>` `>=` `<` `<=` `IN` `CONTAINS` `STARTSWITH` `ENDSWITH` `BETWEEN … AND …`, single- or double-quoted strings, integers, floats, `true`/`false`. Operators are case-insensitive; field names are not.

EQL is a **filter** grammar, not a query language: there is no `SELECT`, no ordering, no vector clause. It parses to the same `VF` tree the Python syntax builds, so it inherits every rejection — an unknown field, an unsupported lookup, or a malformed expression raises `VectorEQLFault` with the character offset, and no string ever reaches elips uninterpreted.

### Guards

`bool(query)` and `len(query)` **raise**, naming the async call to use instead. `if query:` would test object identity (always true) rather than "are there matching records", and `len()` cannot await. This is the same guard the SQL `Q` installs.

```python
if await query.exists(): ...
n = await query.count()
```

An unfiltered `delete()` also raises: emptying a whole collection is almost never what a chained call means.

---

## 5. Interop with the SQL ORM

`aquilia.vectordb` imports `aquilia.models`; **nothing in `aquilia.models` imports `aquilia.vectordb`**. The arrow points one way, which is what keeps `elips` genuinely optional.

### `Link` — pointing at a SQL row

```python
from aquilia.vectordb import Link, resolve

class Document(VectorModel):
    key:     Annotated[str, Key()]
    body:    Annotated[str, Text()]
    post_id: Annotated[int, Link(Post)]

user = await resolve(hit, "post_id")     # one SELECT, explicit
```

Not a foreign key: elips enforces nothing and no join exists. Resolution is always explicit — a descriptor that issued a hidden SELECT on attribute access would turn one loop into N queries with nothing at the call site to suggest it.

### `mirror` — keeping a collection in sync

```python
from aquilia.vectordb import mirror

@mirror(
    into=Document,
    text=lambda p: f"{p.title}\n\n{p.body}",
    meta={"post_id": lambda p: p.pk, "kind": "post"},
    when=lambda p: p.published,
)
class Post(Model):
    ...
```

- **Deterministic keys.** Defaults to `"<table>:<pk>"`, so a re-save overwrites rather than duplicating.
- **Queued by default.** The handler enqueues an `aquilia.tasks` job. A vector write inside a request's transaction would add embedding latency to the response and could not be rolled back with the SQL transaction — a rolled-back save would leave an orphaned vector record. `sync="inline"` is available and is best-effort.
- **`when` gates both ways.** A row that stops qualifying has its vector record removed, so un-publishing a post takes it out of the index rather than leaving a stale copy.
- **Failures are logged, not raised.** A mirror is a derived index; letting it fail the `save()` would roll back a write the user asked for because a secondary index could not be updated.

> **Bulk writes bypass the mirror.** `bulk_create` / `bulk_update` fire no signals, so rows written that way never reach it. `aq vectordb reindex <Model>` is the sanctioned repair.

### `as_models` — hybrid retrieval

Search vectors, return fully-hydrated ORM rows in *relevance* order:

```python
from aquilia.vectordb import as_models

hits = await Document.vectors.query().filter(kind="post").search(text="alpha", limit=20)
posts = await as_models(hits, Post, via="post_id",
                        queryset=Post.query().select_related("author"))
```

One SQL round trip regardless of hit count — primary keys are collected from the hits and fetched with a single `pk__in`, chunked at 999 to respect the SQLite parameter ceiling. Results are then re-sorted in Python by hit index, because SQL `IN` does not preserve argument order and relevance ordering is the entire point. Rows the SQL side no longer has are dropped.

---

## 6. Embedders

An embedder turns text into vectors. Every provider is optional; each raises `VectorEmbedderFault` naming the install command when its backend is missing, rather than failing deep inside a third-party import.

| Provider | Backend | Notes |
|---|---|---|
| `local` | elips built-in | No extra dependency |
| `sentence-transformers` | `sentence-transformers` | Runs in the vdb thread pool |
| `fastembed` | `fastembed` | ONNX, no torch |
| `openai` | `openai` | Network; needs an API key |
| `ollama` | `ollama` HTTP | Local server |
| `callable` | your function | Sync or async |

```python
from aquilia.vectordb import EmbedderOptions

EmbedderOptions(provider="sentence-transformers", model="all-MiniLM-L6-v2", batch_size=32)
EmbedderOptions(provider="openai", model="text-embedding-3-small", api_key=Env("OPENAI_API_KEY"))
EmbedderOptions(provider="ollama", model="nomic-embed-text", base_url="http://localhost:11434")
```

A plain callable needs no configuration object:

```python
from aquilia.vectordb import CallableEmbedder

embedder = CallableEmbedder(my_encode_fn, dimension=384, model="my-model")
```

Every embedder reports a `dimension` and an `EmbeddingLineage` — `(provider, model, revision)` — and both are enforced:

- A vector whose length disagrees with the store raises `VectorDimensionMismatchFault`.
- An embedder whose lineage differs from the one persisted with the collection raises `VectorEmbedderMismatchFault` at bind time.

The second check is the important one. Vectors from two different models occupy incompatible spaces, so mixing them does not degrade results — it makes distances meaningless while still returning a confident-looking ranked list. Changing models is an explicit re-embed (`aq vectordb reembed`), never an implicit one.

Lineage is queryable, so a partially re-embedded collection is diagnosable:

```python
stale = await Document.vectors.query().filter(lineage__model="all-MiniLM-L6-v2").count()
```

---

## 7. Chunking

Long text exceeds an embedder's context window, and one vector per document dilutes the signal of any single passage. A `TextField` may therefore split its text into chunks, each stored as its own record.

```python
class Document(VectorModel):
    key:  str = KeyField()
    body: str = TextField(embed=True, chunk_size=512, chunk_overlap=64, chunker="recursive")
```

| Chunker | Splits on |
|---|---|
| `character` | Fixed windows |
| `recursive` | Paragraphs → lines → sentences → words → characters |
| `sentence` | Sentence boundaries, packed to `chunk_size` |
| `token` | Whitespace tokens |

`recursive` is the default: it tries the largest natural boundary that fits before falling back to a smaller one, so a chunk ends at a paragraph break when it can and mid-word only when it must.

Chunk records carry deterministic keys (`<parent>#<index>`) plus `chunk_index`, `chunk_count`, `chunk_start`, and `chunk_end` provenance, so a hit can be traced to its offset in the source text:

```python
from aquilia.vectordb import parent_key_of, is_chunk_key

hit = (await Document.vectors.search("alpha"))[0]
if is_chunk_key(hit.key):
    print(parent_key_of(hit.key), hit.chunk_start, hit.chunk_end)
```

Deterministic keys are what make a re-save overwrite the previous chunks rather than accumulate a second copy. `chunk_overlap` must be smaller than `chunk_size`; equal or larger cannot advance and raises `VectorChunkingFault` at declaration rather than looping at ingest.

---

## 8. GPU acceleration

Aquilia owns no kernels. elips owns the backend abstraction and the fallback chain; `aquilia.vectordb` translates policy and reports capability.

```python
GpuOptions(policy="prefer_gpu", device=0, fallback="warn")
```

| `policy` | Boot behaviour |
|---|---|
| `cpu_only` | Never attaches a GPU config. |
| `prefer_gpu` | Uses a device when present, logs and runs on CPU otherwise. |
| `require_gpu` | **Boot fails** if no usable device exists. |

Two capability states are tracked separately and never collapsed:

- **`built`** — the elips wheel carries GPU bindings (compile-time).
- **`available`** — a device is actually present (runtime).

A GPU-enabled wheel on a machine with no device is a normal, supported state; reporting it as one boolean makes that case undiagnosable. `require_gpu` failures name which precondition failed.

elips falls back to CPU **per query**, even under `require_gpu` (ADR-GPU-008), so "same API, possibly slower" is the default contract. For deployments where that is unacceptable, `fallback="require"` inspects the query plan and raises `VectorGpuFault` when it ran on CPU. That check is opt-in because it costs an `explain` per query.

```bash
aq vectordb gpu          # probe capability and show the resolved policy
```

---

## 9. Runtime and operations

### Threading

elips is a synchronous C++ extension that releases the GIL on its hot paths, so blocking calls are offloaded to a dedicated `ThreadPoolExecutor` (`aquilia-vdb`) rather than the default executor. A long `compact()` must not starve unrelated `run_in_executor` callers, and named threads make a stalled vector operation identifiable in a stack dump.

`pool_threads` defaults to 4 and is not a throughput knob: elips is single-writer per directory and serializes writes inside C++ however many threads submit them. Reads parallelize, and that is what the 4 is for.

### Single-writer lock

> **elips takes an exclusive lock per database directory.** Running more than one worker against the same store path makes every worker after the first fail to acquire it.

This is why `VectorDBSubsystem` sets `_required = True` **whenever stores are configured** — overriding the usual optional-subsystem default. A vector store that silently failed to open answers every search with an empty list, which reads as "no results" rather than "broken". Booting is refused instead.

An app with no `vectordb` block boots exactly as before, and `_required` stays `False`.

### Boot order

Priority **28** — after storage (25), before database (30). Vector stores may live under a storage-managed path; nothing in the SQL ORM is needed to open one.

### Health

One aggregate `vectordb` entry plus `vectordb.<alias>` per store, so an outage on one store is visible instead of hidden behind a blanket status.

### CLI

```bash
aq vectordb status        # configured stores + elips availability (opens nothing)
aq vectordb gpu           # capability probe and resolved policy
aq vectordb models        # registered models and their slot routing
aq vectordb inspect       # open each store, report live health
aq vectordb stats         # per-collection counts, tombstones, codec
aq vectordb compact       # reclaim space from deleted records
aq vectordb vacuum        # release free pages
aq vectordb compress      # train a quantization codebook and compress
aq vectordb reindex Post  # rebuild a mirrored collection from SQL
aq vectordb reembed       # re-embed a collection under a new model
```

Every command takes `--json` for scripting. `status` reads configuration only and takes no lock, so it stays safe against a live serving directory. `inspect` and the maintenance commands do open the store and will fail while a server holds it — that is the lock working, not a bug.

`compress` and `reembed` rewrite records, so both require `--yes` (or a TTY confirmation) and report what they touched. `reembed` refuses to run without an explicitly named target model: re-embedding under whatever happens to be configured is how a collection ends up with two incompatible vector spaces.

### Quantization

Compression trades recall for memory. It is opt-in per store:

```python
from aquilia.vectordb import QuantizationConfig

QuantizationConfig(codec="pq", pq_bits=8, sample_size=10_000)
```

`Hit.approximate` is `True` when a distance was computed from a reconstructed vector, and `Hit.codec` names the codec. A caller applying a score threshold deserves to know it is thresholding on an estimate, so this is surfaced rather than hidden.

---

## 10. Faults

Every failure is a `VectorFault` subclass with a stable `code`. Assert on the code, never the message text.

| Code | Raised when |
|---|---|
| `VECTOR_NOT_INSTALLED` | `elips` is missing |
| `VECTOR_SCHEMA_INVALID` | Bad model declaration, or a dimension/metric mismatch at bind |
| `VECTOR_VALIDATION_FAILED` | Constraint, dimension, or unknown-attribute failure |
| `VECTOR_ENCODING_FAILED` | A payload value could not be encoded |
| `VECTOR_QUERY_INVALID` | Query misuse — truthiness, `len()`, unfiltered delete |
| `VECTOR_LOOKUP_UNSUPPORTED` | `__isnull`, a non-orderable range, an unknown suffix |
| `VECTOR_NOT_FOUND` / `VECTOR_MULTIPLE_FOUND` | `one()` matched zero / more than one |
| `VECTOR_STORE_ERROR` | Underlying elips storage failure |
| `VECTOR_LOCK_CONFLICT` | Another process holds the writer lock |
| `VECTOR_DIMENSION_MISMATCH` | Vector length disagrees with the store |
| `VECTOR_CONFIG_INVALID` | Bad or inconsistent store configuration |
| `VECTOR_EMBEDDER_UNAVAILABLE` | Text operation without a configured embedder |
| `VECTOR_EMBEDDER_MISMATCH` | Embedder fingerprint differs from the persisted one |
| `VECTOR_REGISTRY_ERROR` | Unknown store alias, or use before boot |
| `VECTOR_GPU_UNAVAILABLE` | `require_gpu` cannot be satisfied |
| `VECTOR_GPU_FALLBACK` | `fallback="require"` and the query ran on CPU |
| `VECTOR_EQL_INVALID` | An EQL string failed to parse |
| `VECTOR_CHUNKING_INVALID` | Bad chunker configuration |
| `VECTOR_INGEST_FAILED` | An ingest or re-embed operation failed |

---

## 11. Migration and limits

There is no legacy vector API to migrate from. Adoption is additive:

1. `pip install 'aquilia[vectordb]'`
2. Add `.vectordb(stores={...})` to `workspace.py`
3. Declare models in `modules/<app>/vector_models.py`

Nothing existing changes. `VectorModel` and `Model` coexist in one module and are disjoint under `isinstance`.

**Changing `dimension`, `metric`, or the embedder on an existing store is not a migration.** elips persists that identity on disk and refuses a reopen that disagrees. Re-embedding every record is expensive and lossy by choice, so it stays an explicit operator action rather than an auto-migrate flag — the same stance the SQL ORM's startup guard takes.

### Out of scope

- Networked or distributed vector storage — elips is embedded-only by design.
- Storing vectors in SQL tables. `as_models` hydrates; it does not mirror vectors into SQL.
- Any GPU kernel or FAISS port.
- Automatic re-embedding on an embedder change. `aq vectordb reembed` stays an operator action.
- Ordering in scan mode. Without a query vector there is nothing to rank by.
