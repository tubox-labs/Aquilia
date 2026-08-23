# Vector Database Subsystem (`aquilia.vectordb`)

Aquilia v1.4.0 introduces `aquilia.vectordb`, a typed vector storage and similarity-search subsystem backed by the embedded [elips](https://pypi.org/project/elips/) C++ engine. It ships as an optional extra (`pip install 'aquilia[vectordb]'`).

---

## Declarative Model Layer (`VectorModel`)

Vector collections are declared similarly to SQL ORM models, with slot routing resolved at class creation time.

```python
from datetime import datetime
from aquilia.vectordb import (
    VectorModel, Field, KeyField, TextField, VectorField, ScoreField
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

### Unified Field Descriptors
* **`KeyField`:** Record identifier with optional automatic prefixing (`doc_123`).
* **`VectorField`:** Float vector payload carrying dimension and distance metric metadata.
* **`TextField`:** Text content with automatic embedding and chunking options.
* **`Field` / `PayloadField`:** Metadata payload with validation constraints (`ge`, `le`, `pattern`, `choices`, etc.).
* **`ScoreField`:** Populated dynamically with distance/similarity score upon search.
* **`LinkField`:** References a SQL model row without requiring database foreign keys.

---

## Query Engine & Filtering

Aquilia VectorDB provides four interchangeable filter syntaxes that all compile into the same validated `CompiledFilter` AST:

### 1. Keyword Lookups
```python
hits = await Document.vectors.search("release notes", limit=10).filter(views__gte=10, source="web")
```

### 2. `VF` Filter Trees (Boolean Logic)
```python
from aquilia.vectordb import VF

hits = await Document.vectors.search("release notes").filter(
    VF.or_(VF.eq("source", "docs"), VF.and_(VF.gte("views", 100), VF.eq("source", "blog")))
)
```

### 3. Operator-Overloaded Field Expressions
```python
hits = await Document.vectors.search("release notes").filter(
    (Document.source == "docs") | ((Document.views >= 100) & (Document.source.in_(["blog", "wiki"])))
)
```

### 4. EQL (Embedded Query Language)
Safe string filter grammar for queries originating from config, admin dashboards, or HTTP parameters:
```python
hits = await Document.vectors.filter_eql('source == "docs" AND views >= 100').search("release notes")
```

---

## Embedders & Text Chunking

* **Pluggable Embedders:** Built-in adapters for `LocalEmbedder`, `SentenceTransformersEmbedder`, `FastEmbedder`, `OpenAIEmbedder`, `OllamaEmbedder`, and custom `CallableEmbedder`.
* **Embedding Lineage:** Stores `provider`, `model`, and `revision` alongside the collection to prevent dimension mismatches.
* **Deterministic Chunking:** `character`, `recursive`, and `sentence` chunkers that generate provenance keys (`<parent>#<chunk_index>`) with offset tracking (`parent_key_of()`, `is_chunk_key()`).

---

## Quantization & Compression

Reduce vector memory footprints with minimal recall trade-offs:
* **`sq8` (Scalar Quantization):** ≈4× memory reduction.
* **`pq` / `opq` (Product Quantization):** ≈8–32× memory reduction.
* Hits returned from compressed stores carry `approximate=True` and report their `codec`.

---

## SQL-ORM Mirroring & Hybrid Retrieval

* **`@mirror` Decorator:** Automatically synchronizes vector collections with SQL tables via background tasks:
  ```python
  @mirror(Document, sql_model=ArticleModel, text_fields=["content"], sync_on_save=True)
  class ArticleModel(Model):
      id = AutoField(primary_key=True)
      content = TextField()
  ```
* **`as_models()` Hybrid Retrieval:** Fetches primary keys from vector search and executes **a single SQL `IN` query** to hydrate real ORM model instances sorted by semantic relevance.

---

## `aq vectordb` CLI Command Suite

```bash
aq vectordb status                 # Inspect configured stores and driver status
aq vectordb models                 # List registered vector models and slot routing
aq vectordb inspect [STORE]        # Check live store health and indexes
aq vectordb stats [STORE]          # Record counts, tombstone ratio, WAL depth
aq vectordb compact [STORE]        # Reclaim deleted record space
aq vectordb vacuum [STORE]         # Release free pages to filesystem
aq vectordb compress [STORE]       # Train quantization codebook in-place
aq vectordb reindex MODEL          # Rebuild vector collection from SQL table
aq vectordb reembed --model M      # Re-embed collection under a new model
```
