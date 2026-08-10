# `aq vectordb` Command Reference — v1.4.0b3

A new CLI group registered in `aquilia/cli/__main__.py` and categorised under **Database** in `aq --help` (`aquilia.cli.core.registry._CATEGORIES["vectordb"] = "Database"`).

```bash
aq vectordb --help
```

Nothing in this group is a breaking change — the whole group is new.

---

## Lock discipline

elips is **single-writer per database directory**. The commands split cleanly on whether they take that lock:

| Takes no lock | Takes the writer lock |
|---|---|
| `status` | `inspect`, `stats`, `compact`, `vacuum`, `compress`, `reindex`, `reembed` |
| `gpu` (probe only; reads config for policy display) | |
| `models` (imports model modules; opens nothing) | |

The lock-taking commands **will fail while a server holds the same store**. That is the lock working, not a bug. Run them during a maintenance window, or point them at a store the server does not own.

---

## `aq vectordb status`

Show configured stores and `elips` availability. Reads configuration only.

```
--json    Output as JSON
```

```bash
$ aq vectordb status
Vector store status
✔ elips available (version 1.1.0)

 * default
     path       ./.aquilia/vectors/default
     dimension  384   metric cosine   index hnsw
     gpu        prefer_gpu
     embedder   local
   images
     path       ./.aquilia/vectors/images
     dimension  512   metric l2   index flat
     gpu        cpu_only
     embedder   none

* = default store
```

Without the driver:

```bash
$ aq vectordb status
Vector store status
! elips not installed — vector stores cannot open
  No module named 'elips'
  Install with: pip install 'aquilia[vectordb]'
```

Without configuration:

```bash
$ aq vectordb status
Vector store status
✔ elips available (version 1.1.0)

i No vector stores configured.
  Add Workspace.vectordb(stores={...}) to your workspace.py
```

JSON payload shape:

```json
{
  "elips": { "available": true, "version": "1.1.0" },
  "enabled": true,
  "default": "default",
  "stores": [ { "alias": "default", "path": "...", "dimension": 384, "...": "..." } ]
}
```

---

## `aq vectordb gpu`

Probe GPU capability and show the resolved policy per store.

```
-s, --store TEXT   Resolve policy for one store alias
    --json         Output as JSON
```

`built` (the elips wheel carries GPU bindings — compile-time) and `available` (a device is actually present — runtime) are reported **separately**. A GPU-enabled build on a machine with no device is a normal, supported state; collapsing the two into one boolean makes that case impossible to diagnose.

```bash
$ aq vectordb gpu
GPU capability
  built      True
  available  True

  [0] NVIDIA RTX A4000  (cuda)
       memory 15.73 GiB   fp16 True   unified False

Configured policy
  default: policy=prefer_gpu fallback=warn — ok
  images: policy=cpu_only fallback=warn — ok
```

`require_gpu` with no device is called out explicitly, because it is a boot failure rather than a slow path:

```
  default: policy=require_gpu fallback=error — BOOT WILL FAIL (require_gpu, no device)
```

Exits `1` when `elips` is not installed — there is nothing to probe.

---

## `aq vectordb models`

List registered vector models and their slot routing.

```
--json    Output as JSON
```

Slot routing is resolved at class creation and is not visible in the source, so this is the fastest way to confirm a `KeyField` / `TextField` / `VectorField` (or a legacy `Key()` / `Text()` / `Dimension()` marker) landed where the author intended.

```bash
$ aq vectordb models
Vector models
  modules.blog.vector_models.Document
     collection documents   store default   dim 384
     key=key  text=body  vector=vector
     payloads   created_at, source, views
     links      author_id
```

```bash
$ aq vectordb models
Vector models
i No vector models registered.
  Declare them in modules/<app>/vector_models.py or a manifest's vector_models list.
```

---

## `aq vectordb inspect [STORE]`

Open each store and report live health.

```
STORE     Optional store alias; all stores when omitted
--json    Output as JSON
```

```bash
$ aq vectordb inspect default
Vector store inspection
✔ default: healthy
     path            ./.aquilia/vectors/default
     dimension       384
     metric          cosine
     index           hnsw
     collections     ['documents']
     pending_writes  0
     gpu             built=True available=True
```

Every store is closed again on the way out, including on failure — the `finally` calls `VectorRegistry.shutdown()`, so the lock is released even when one store errors.

---

## `aq vectordb stats [STORE]`

Per-collection telemetry: record counts, tombstones, codec, WAL depth.

```
STORE     Optional store alias
--json    Output as JSON
```

```bash
$ aq vectordb stats
Vector store statistics
✔ default
     pending_writes  0
     documents
        live=12403  tombstone_ratio=0.04  dim=384  metric=cosine  codec=none
```

`tombstone_ratio` is the signal for whether `compact` is worth running.

---

## `aq vectordb compact [STORE]`

Reclaim space held by deleted records.

```
STORE     Optional store alias
```

```bash
$ aq vectordb compact default
compact default ...
✔ Compacted 1 store(s).
```

Refuses a `read_only` store and exits `1`:

```
✘ default: store is read_only; refusing to compact
```

---

## `aq vectordb vacuum [STORE]`

Release free pages back to the filesystem. Same shape and same `read_only` refusal as `compact`.

```bash
$ aq vectordb vacuum
vacuum default ...
✔ Vacuumed 1 store(s).
```

---

## `aq vectordb compress [STORE]`

Train a quantization codebook and compress a store in place.

```
STORE                  Optional store alias
--codec [pq|opq|sq8]   Quantization codec to train and apply  [default: pq]
--sample-size INT      Vectors sampled to train the codebook  [default: 10000]
--pq-dim INT           Sub-quantizer count (pq/opq)
--pq-bits INT          Bits per sub-quantizer code (4-8)
--yes                  Skip the confirmation prompt
```

Trades recall for memory: `sq8` stores one byte per dimension (≈4× smaller); `pq`/`opq` store a short code per vector (≈8–32× smaller). Distances become approximate afterwards, which is why every hit carries `approximate=True` and its codec.

**Not reversible in place.** Compression frees the full-precision vectors once the codebook is trained, so restoring them means re-ingesting or re-embedding. Hence the confirmation:

```bash
$ aq vectordb compress default --codec sq8
Compress with sq8? Full-precision vectors are discarded and distances become approximate. [y/N]: y
compressing default/documents with sq8 ...
✔ Compressed 1 store(s) with sq8.
```

Scriptable with `--yes`. Refuses a `read_only` store.

---

## `aq vectordb reindex MODEL`

Rebuild a mirrored collection from its SQL table.

```
MODEL                    SQL model class name, e.g. Post  (required)
-b, --batch-size INT     Rows per write batch  [default: 500]
```

This is the sanctioned repair for the bulk-write blind spot: `bulk_create` and `bulk_update` fire no signals, so rows written that way never reach `@mirror` and the vector collection silently drifts.

```bash
$ aq vectordb reindex Post
✔ Reindexed 8412 record(s) from Post.
```

Exits `1` with a named reason when the model is unknown or carries no `@mirror`:

```
✘ Post has no @mirror registered — nothing to reindex.
```

---

## `aq vectordb reembed`

Re-embed a collection under a different embedding model.

```
-m, --model TEXT         Vector model class name, e.g. Document  (required)
    --to-embedder TEXT   Target embedder URI  (required)
-b, --batch-size INT     Records per batch  [default: 200]
    --dry-run            Report what would change, write nothing
```

Reads every record's stored text, embeds it with the new model, and writes the vector back **under the same key** — so keys, payloads, and any SQL links survive the migration.

```bash
$ aq vectordb reembed --model Document --to-embedder openai/text-embedding-3-large --dry-run
i Dry run: 12403 record(s) would be re-embedded with openai/text-embedding-3-large.

$ aq vectordb reembed --model Document --to-embedder openai/text-embedding-3-large
✔ Re-embedded 12403 record(s) with openai/text-embedding-3-large.
! 17 record(s) had no stored text and were left unchanged.
```

Two failure modes it guards against:

1. **A dimension change** (384 → 1536) cannot be applied in place, because elips holds dimension database-global. The command refuses rather than writing vectors the store cannot index, and names the store to reconfigure:

   ```
   ✘ openai/text-embedding-3-large produces 3072-dimension vectors but store 'default' is configured for 384.
     elips holds dimension database-global, so this cannot be changed in place.
   ```

2. **A record with no stored text** cannot be re-embedded from anything. Those are counted and reported rather than silently left on the old model, which would leave the collection split across two vector spaces.

`--to-embedder` is **required**: re-embedding under whatever happens to be configured is exactly how a collection ends up with two incompatible vector spaces. A model with no text field is rejected outright.

---

## Common workflows

### Bring up vector search on an existing app

```bash
pip install 'aquilia[vectordb]'
# add .vectordb(stores={...}) to workspace.py
# add modules/<app>/vector_models.py

aq vectordb status      # driver installed? stores read correctly?
aq vectordb models      # slot routing as intended?
aq doctor               # picks up the vectordb.driver check
aq serve
```

### Diagnose an empty search result set

```bash
aq vectordb models              # is the model registered at all?
aq vectordb stats               # does the collection hold records?
aq vectordb inspect             # is the store healthy, dimension as expected?
```

### Repair drift after a bulk import

```bash
aq vectordb reindex Post
aq vectordb stats
```

### Maintenance window

```bash
aq vectordb stats               # check tombstone_ratio
aq vectordb compact
aq vectordb vacuum
aq vectordb compress --codec sq8 --yes    # only if memory is the constraint
```

### Migrate embedding models

```bash
# 1. Reconfigure the store's dimension in workspace.py if the new model differs.
# 2. Dry run first.
aq vectordb reembed --model Document --to-embedder openai/text-embedding-3-small --dry-run
# 3. Apply.
aq vectordb reembed --model Document --to-embedder openai/text-embedding-3-small
```

---

## Anti-patterns

| Don't | Do |
|---|---|
| Run `aq vectordb inspect` against a live server's store | Use `aq vectordb status`, which takes no lock |
| Run `workers > 1` against one store path | Separate paths per worker, or `read_only=True` for search-only workers |
| Change `dimension` in config and expect the store to follow | Reconfigure the store, then `aq vectordb reembed` |
| `aq vectordb compress` on a store you cannot re-ingest | Verify a backup or a re-ingest path exists first — compression is one-way |
| Parse the human output in CI | Every command takes `--json` |

---

## Related documentation

- [`vectordb.md`](vectordb.md) — subsystem overview, architecture, configuration
- [`docs/vectordb.md`](../../docs/vectordb.md) — complete API reference
- [`cli_modernization.md`](cli_modernization.md) — `ExitCode` contract these commands exit under
- [`checks_engine.md`](checks_engine.md) — the `vectordb.driver` health check
