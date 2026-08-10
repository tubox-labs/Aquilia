# Vector Database Subsystem — v1.4.0b3

`aquilia.vectordb` is a new first-class subsystem: a typed model layer over [elips](https://pypi.org/project/elips/), an embedded vector database. It gives vector collections the same declarative shape Aquilia's SQL ORM gives tables — models, managers, queries, faults, subsystem lifecycle, CLI — without pretending the two storage engines are the same thing.

Full reference: [`docs/vectordb.md`](../../docs/vectordb.md).

---

## Overview

| Aspect | Value |
|---|---|
| Package | `aquilia.vectordb` (24 modules) |
| Driver | `elips >= 1.1.0` — **optional extra** |
| Install | `pip install 'aquilia[vectordb]'` |
| Config | `Workspace.vectordb(...)`, `Integration.vectordb(...)`, `AquilaConfig.VectorDB` |
| Manifest | `AppManifest.vector_models`, `ComponentKind.VECTOR_MODEL` |
| Subsystem | `VectorDBSubsystem` — priority 28, timeout 60s |
| CLI | `aq vectordb` (10 subcommands) |
| Health check | `vectordb.driver` → `AQ_VECTORDB_DRIVER_MISSING` |

---

## Motivation

Retrieval-augmented workloads had no home in Aquilia. Applications that wanted similarity search bolted a client library onto a service, hand-rolled serialization between the ORM and the vector store, and had no boot-time validation, no health reporting, no CLI, and no fault taxonomy. Two problems followed:

1. **Silent wrongness.** A vector written under one embedding model and searched under another returns a confidently ranked list of meaningless results. Nothing in a hand-rolled client notices.
2. **No lifecycle.** A store that failed to open answered every search with an empty list, which reads as "no results" rather than "broken".

The subsystem exists to make both loud.

---

## Design goals

- **Optional at every level.** `elips` is a C++ extension. Importing `aquilia.vectordb` on an install without it succeeds; the fault surfaces at first *use* as `VectorNotInstalledFault` carrying the install hint. Nothing in the package imports `elips` at module scope.
- **One-way dependency.** `aquilia.vectordb` imports `aquilia.models`; nothing in `aquilia.models` imports `aquilia.vectordb`. That arrow is what keeps the extra genuinely optional.
- **Loud over lossy.** Dimension mismatches, embedder-lineage mismatches, nested payloads, and unsupported lookups are rejected — most of them at class-creation time — rather than coerced.
- **Same shapes as the ORM.** `VectorModel`/`Model`, `VectorQuery`/`Q`, `VectorRegistry`/`ModelRegistry`, `VectorFault`/`Fault`. Nothing new to learn where nothing new is happening.

---

## Architecture

```
aquilia/vectordb/
├── __init__.py      # Lazy re-exports (_LAZY_ATTRS) — elips never touched on import
├── _compat.py       # is_available(), require_elips()
├── metaclass.py     # VectorModelMeta — slot routing, registration at class creation
├── base.py          # VectorModel, VectorState
├── fields.py        # KeyField/VectorField/TextField/Field/ScoreField/LinkField
├── annotations.py   # Legacy Annotated markers (Key, Dimension, Text, Payload, …)
├── schema.py        # VectorSchema, VectorOptions, PayloadSpec
├── codecs.py        # Python type ↔ elips MetaValue codecs
├── manager.py       # VectorManager (`Model.vectors`)
├── query.py         # VectorQuery, Hit
├── filters.py       # VF trees → CompiledFilter
├── expressions.py   # FieldExpression (Document.views >= 10)
├── eql.py           # parse_eql — string filter grammar
├── embedders.py     # local / sentence-transformers / fastembed / openai / ollama / callable
├── chunking.py      # character / recursive / sentence / token chunkers
├── configs.py       # VectorStoreConfig, GpuOptions, EmbedderOptions, QuantizationConfig
├── engine.py        # VectorEngine — one elips database
├── pool.py          # VectorPool — the `aquilia-vdb` thread pool
├── registry.py      # VectorRegistry — models, stores, live engines
├── gpu.py           # probe(): built vs available, DeviceInfo
├── interop.py       # Link, resolve, mirror, as_models, reindex
├── faults.py        # VectorFault hierarchy (21 codes)
├── signals.py       # vector_pre_save / post_save / pre_delete / post_delete
└── subsystem.py     # VectorDBSubsystem — BootContext lifecycle
```

### Boot position

`VectorDBSubsystem` declares priority **28** — after storage (25), before database (30). Vector stores may live under a storage-managed path, so storage settles first; nothing in the SQL ORM is needed to open one, so it does not wait on the database. `_timeout` is **60 seconds** rather than the usual default: opening a store rebuilds its index, which is slower than a socket connect.

### Conditional required-ness

`_required` starts `False` and is raised to `True` inside `_do_initialize` **only when stores are actually configured**:

```python
stores = config.get("stores") or []
if not stores:
    logger.warning("vectordb is enabled but declares no stores — nothing to open")
    return

# A declared store that fails to open must stop the boot.
self._required = True
```

An app with no `vectordb` block boots exactly as before. An app that *declared* a store and could not open it fails loudly — see [Edge cases](#edge-cases).

> **`required` is only final after `initialize()` returns.** Read before that, it holds the class default. `BaseSubsystem` now documents this contract explicitly; see [Subsystem boot contract](subsystem_boot_contract.md).

---

## How it works internally

### 1. Declaration → schema

`VectorModelMeta` resolves every attribute to exactly one **slot** at class creation: key, vector, text, payload, or score. Two interchangeable declaration styles compile to the same `VectorSchema`.

```python
from datetime import datetime
from aquilia.vectordb import (
    VectorModel, Field, KeyField, VectorField, TextField, ScoreField,
)

class Document(VectorModel):
    key:        str          = KeyField(prefix="doc_")
    body:       str          = TextField(embed=True, min_length=1, max_length=8192)
    vector:     list[float]  = VectorField(dimension=384)
    source:     str          = Field(default="web", indexed=True, max_length=256)
    views:      int          = Field(default=0, ge=0)
    score:      float | None = ScoreField()
    created_at: datetime     = Field(default_factory=datetime.utcnow)

    class Meta:
        collection = "documents"
        store = "default"
        dimension = 384
```

Class access returns the **field** (so `Document.views >= 10` builds a filter); instance access returns the **value**. Declaring a field in both the assignment and an `Annotated[...]` position for one attribute raises `VectorSchemaFault` — there is no principled winner, so the contradiction is rejected rather than resolved by precedence.

### 2. Discovery → registration

`RuntimeRegistry` gained a scan and an import pass that mirror the SQL model path:

- `_discover_vector_models(ctx)` scans `modules/<app>/vector_models.py` and `modules/<app>/vector_models/*.py`, appending paths to `AppContext.vector_models`.
- `_register_vector_models()` imports them so `VectorModelMeta` self-registers into `VectorRegistry`.

A **separate directory** rather than a marker inside `models/` is deliberate: importing a vector model imports `aquilia.vectordb`, and scanning `models/` for them would drag the optional dependency into every app that has SQL models. Keeping the paths disjoint keeps that cost opt-in.

Nothing is imported at all when no module declares a vector model, so an app without them never touches `aquilia.vectordb`.

### 3. Config → stores

`VectorDatabaseIntegration.to_dict()` normalizes `{alias: config}` into a list of entries each carrying its own `alias`, matching `StorageIntegration.to_dict()`. Store-level settings win over integration-level defaults: the outer values exist so the common case (one path, one GPU policy) is declared once, not so they override a store that was explicit.

`VectorRegistry.configure(stores, default=..., pool_threads=...)` installs that configuration. Engines open lazily, one per alias, on first `VectorRegistry.engine(alias)`.

### 4. Binding validation

elips holds `dimension` and `metric` **database-global**: they are set once at `connect()` and every vault inherits them. `VectorRegistry._validate_binding()` therefore checks each model against its store's configuration and fails loudly on a mismatch, naming both sides. Coercing the model to the store's dimension would write vectors that search returns in the wrong order, with nothing in the logs.

---

## Usage guide

### Configuration — `workspace.py`

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

`Workspace.vectordb()` is shorthand for `integrate(VectorDatabaseIntegration(...))`. Both record into `Workspace._integrations["vectordb"]` and surface at `config["vectordb"]` plus `config["integrations"]["vectordb"]`.

### Configuration — `aquilia.config.py`

```python
from aquilia.pyconfig import AquilaConfig

class BaseEnv(AquilaConfig):
    class vectordb(AquilaConfig.VectorDB):
        enabled   = True
        path      = "./.aquilia/vectors"
        dimension = 384
        embedder  = "sentence-transformers/all-MiniLM-L6-v2"

class ProdEnv(BaseEnv):
    env = "prod"

    class vectordb(BaseEnv.vectordb):
        embedder     = "openai/text-embedding-3-small"
        dimension    = 1536
        auto_create  = False     # a missing store is a boot failure
        quantization = "sq8"     # 4x smaller, approximate distances
```

`AquilaConfig.VectorDB` defaults to `enabled = False`. `ConfigLoader.get_vectordb_config()` returns the same defaults, so an absent block never makes the subsystem try to load the extension.

### Manifest declaration

```python
# modules/blog/manifest.py
from aquilia.manifest import AppManifest

manifest = AppManifest(
    name="blog",
    version="1.0.0",
    models=["modules.blog.models:Post"],
    vector_models=["modules.blog.vector_models:Document"],
)
```

`vector_models` is kept separate from `models` because the two are bound to different backends — a `VectorModel` has no table and never appears in a SQL migration. `auto_discovery` now includes `"vector_models"` by default.

### Reading and writing

```python
doc = Document(vector=[...], body="release notes", source="docs", views=0)
await doc.save()            # key assigned if absent
await doc.refresh()
await doc.delete_instance()

hits = await Document.vectors.query().filter(source="docs").search(vector=q, limit=10)
for hit in hits:
    print(hit.score, hit.body, hit.approximate)
```

### Hybrid retrieval with the SQL ORM

```python
from aquilia.vectordb import as_models, mirror, resolve

@mirror(into=Document,
        text=lambda p: f"{p.title}\n\n{p.body}",
        meta={"post_id": lambda p: p.pk, "kind": "post"},
        when=lambda p: p.published)
class Post(Model):
    ...

hits  = await Document.vectors.query().filter(kind="post").search(text="alpha", limit=20)
posts = await as_models(hits, Post, via="post_id",
                        queryset=Post.query().select_related("author"))
```

`as_models` issues **one** SQL round trip regardless of hit count: primary keys are collected from the hits and fetched with a single `pk__in`, chunked at 999 to respect the SQLite parameter ceiling, then re-sorted in Python by hit index because SQL `IN` does not preserve argument order.

---

## CLI

See [`vectordb_cli.md`](vectordb_cli.md) for full flag-by-flag coverage.

```bash
aq vectordb status        # configured stores + elips availability (opens nothing)
aq vectordb gpu           # capability probe and resolved policy per store
aq vectordb models        # registered models and their slot routing
aq vectordb inspect       # open each store, report live health
aq vectordb stats         # per-collection counts, tombstones, codec, WAL depth
aq vectordb compact       # reclaim space from deleted records
aq vectordb vacuum        # release free pages
aq vectordb compress      # train a quantization codebook and compress
aq vectordb reindex Post  # rebuild a mirrored collection from SQL
aq vectordb reembed       # re-embed a collection under a new model
```

---

## Performance implications

| Concern | Behaviour |
|---|---|
| **Import cost on installs without vectordb** | Zero. `_LAZY_ATTRS` defers `engine`, `gpu`, `interop`, `embedders`, `eql`, `chunking` and `subsystem` to first attribute access. Discovery imports nothing when no module declares a vector model. |
| **Blocking C++ calls** | Offloaded to a dedicated `ThreadPoolExecutor` named `aquilia-vdb` rather than the default executor, so a long `compact()` cannot starve unrelated `run_in_executor` callers, and a stalled vector op is identifiable in a stack dump. |
| **`pool_threads`** | Defaults to 4. **Not a write-throughput knob** — elips is single-writer per directory and serializes writes inside C++ however many threads submit them. Reads parallelize; that is what the 4 is for. |
| **Store open latency** | Opening rebuilds the index, hence the 60s subsystem timeout. A large `hnsw` store dominates boot time; `flat` opens near-instantly. |
| **Quantization** | `sq8` ≈ 4× smaller, `pq`/`opq` ≈ 8–32× smaller, both with approximate distances. `Hit.approximate` and `Hit.codec` surface that to callers applying a score threshold. |
| **`as_models`** | O(1) SQL queries per call, not O(hits). |
| **Scan mode** | `all()`/`count()` filter on metadata only and return insertion order. Key-attribute and `lineage__*` lookups are evaluated in Python against hydrated records — correct, but they scan rather than narrow the index. |

---

## Edge cases

**Single-writer lock.** elips takes an exclusive lock per database directory. Running more than one worker against the same store path makes every worker after the first fail to acquire it — a startup fault (`VectorLockFault`), not a degradation. This is the practical reason `_required` is raised when stores are declared: a degraded boot would hide it.

**`workers > 1`.** Either give each worker its own store path, or set `read_only=True` on the shared store so workers search without the writer lock. Writes then raise.

**`auto_create=False`.** A missing store directory fails the boot instead of serving an empty index. Recommended in production.

**Dimension/metric change on an existing store.** Not a migration. elips persists that identity on disk and refuses a reopen that disagrees. `aq vectordb reembed` refuses a dimension change in place and names the store to reconfigure.

**Embedder change.** Vectors from two models occupy incompatible spaces, so mixing them does not degrade results — it makes distances meaningless while still returning a confident-looking ranked list. `VectorEmbedderMismatchFault` fires at bind time. Re-embedding is an explicit operator action, never implicit.

**Python 3.10.** `elips 1.1.0` publishes no cp310 wheels. The extra carries `python_version >= '3.11'`, so on 3.10 it installs nothing and `aquilia.vectordb` degrades exactly as on any install without the driver — `VectorNotInstalledFault` at first use. Without that marker, `aquilia[full]` would become unresolvable on 3.10 rather than simply omitting vector support.

**`__isnull` lookups.** Rejected with `VectorLookupFault`. elips has no null concept — an absent metadata key simply fails to match any predicate — so neither `True` nor `False` has a faithful translation. Model absence with a sentinel or a boolean flag.

**Range filters over `Decimal`/`UUID`/`bytes`.** Rejected. These encode to strings where lexicographic order is not value order (`"9" > "10"`). Equality and `__in` still work.

**Nested `dict`/`list` payloads.** Rejected at class creation, not on first write — a store half-populated with unreadable values is much harder to recover from than an import error.

**Bulk writes bypass `@mirror`.** `bulk_create`/`bulk_update` fire no signals. `aq vectordb reindex <Model>` is the sanctioned repair.

**GPU per-query fallback.** elips falls back to CPU per query even under `require_gpu`, so "same API, possibly slower" is the default contract. `fallback="require"` inspects the query plan and raises `VectorGpuFault` when it ran on CPU; that check is opt-in because it costs an `explain` per query.

---

## Wiring the store lifecycle

`AquiliaServer` boots storage, cache, tasks, mail and effects through its own ordered `_setup_*` methods; it does **not** orchestrate `BootContext` subsystems. `VectorDBSubsystem` is therefore driven by the host — an embedder, an alternative runner, a test, or a module lifecycle hook:

```python
# modules/search/hooks.py
from aquilia.subsystems import BootContext, VectorDBSubsystem

_subsystem = VectorDBSubsystem()

async def on_boot(config, container=None):
    ctx = BootContext(config=config, manifests=[])
    if container is not None:
        ctx.shared_state["container"] = container
    status = await _subsystem.initialize(ctx)
    if status.status.value == "unhealthy" and _subsystem.required:
        raise RuntimeError(f"vectordb failed to boot: {status.message}")

async def on_close(config, container=None):
    await _subsystem.shutdown()
```

```python
# modules/search/manifest.py
from aquilia.manifest import AppManifest, LifecycleConfig

manifest = AppManifest(
    name="search",
    version="1.0.0",
    vector_models=["modules.search.vector_models"],
    lifecycle=LifecycleConfig(
        on_startup="modules.search.hooks:on_boot",
        on_shutdown="modules.search.hooks:on_close",
    ),
)
```

The `aq vectordb` commands configure and shut down `VectorRegistry` themselves, so they work without any of this.

---

## Backward compatibility

Adoption is **purely additive**. There is no legacy vector API to migrate from, and nothing existing changes:

- An install without `elips` behaves exactly as before this release.
- A workspace with no `vectordb` block boots with `VectorDBSubsystem._required = False` and never imports the driver.
- `AppManifest.vector_models` defaults to `[]`; `AppContext.vector_models` defaults to `[]`.
- `VectorModel` and `Model` coexist in one module and are disjoint under `isinstance`.
- The original `Annotated` marker syntax (`Key()`, `Dimension(n)`, `Text()`, `Payload()`, `Score()`, `MinLength`, `MaxValue`, `Range`, …) is fully supported and unchanged; the unified field objects are additive.

---

## Limitations

- **Embedded only.** No networked or distributed vector storage — that is elips's design, not a gap to fill.
- **No vectors in SQL tables.** `as_models` hydrates from SQL; it does not mirror vectors into it.
- **No GPU kernels.** Aquilia owns no kernels; elips owns the backend abstraction and the fallback chain.
- **No automatic re-embedding.** `aq vectordb reembed` stays an operator action.
- **No ordering in scan mode.** Without a query vector there is nothing to rank by, so `order_by` is not offered rather than silently ignored.
- **`offset()` rejected on `search()`.** A similarity index returns top-k, so paging by offset would re-rank between pages.

---

## Related documentation

- [`docs/vectordb.md`](../../docs/vectordb.md) — complete reference (fields, codecs, queries, EQL, embedders, chunking, GPU, faults)
- [`vectordb_cli.md`](vectordb_cli.md) — `aq vectordb` command reference
- [`subsystem_boot_contract.md`](subsystem_boot_contract.md) — `BootContext`, DI resolution, timeout enforcement
- [`checks_engine.md`](checks_engine.md) — the `vectordb.driver` health check
- [`migration.md`](migration.md) — upgrade steps and compatibility matrix
- [`README.md`](README.md) — release overview
