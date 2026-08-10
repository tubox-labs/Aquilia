"""
Vector store CLI commands — ``aq vectordb ...``

Operational surface for the :mod:`aquilia.vectordb` subsystem:

    aq vectordb status       Configured stores, elips availability
    aq vectordb gpu          Probe GPU capability and the resolved policy
    aq vectordb models       Vector models registered from discovery
    aq vectordb inspect      Open each store and report live health
    aq vectordb stats        Per-collection telemetry: counts, tombstones, codec
    aq vectordb compact      Compact a store, reclaiming deleted-record space
    aq vectordb vacuum       Vacuum a store
    aq vectordb compress     Train a quantization codebook and compress
    aq vectordb reindex      Re-mirror a SQL model into its vector collection
    aq vectordb reembed      Re-embed a collection under a new embedding model

Configuration is resolved through the workspace, so what the CLI reports is what
boot would apply — there is no second source of truth.

``elips`` is optional. Commands that only read configuration keep working
without it and say so, which is what makes ``aq vectordb status`` useful as a
first diagnostic on a machine that has not installed it yet.
"""

from __future__ import annotations

import asyncio
import json as jsonlib
import sys
from typing import Any

import click

from aquilia.cli.utils.colors import dim, error, info, section, success, warning


def _load_vectordb_config() -> dict[str, Any]:
    """
    Resolve the ``vectordb`` configuration block from the workspace.

    Returns an empty dict when the workspace declares none, which callers render
    as a hint rather than an error.
    """
    from aquilia.cli.core.workspace import load_workspace

    ws = load_workspace()
    if ws.workspace_obj is None:
        return {}

    try:
        config = ws.workspace_obj.to_dict()
    except Exception:
        return {}

    return config.get("vectordb") or {}


def _load_configs(store: str | None = None) -> list[Any]:
    """Return :class:`VectorStoreConfig` objects for the configured stores."""
    from aquilia.vectordb.configs import VectorStoreConfig, normalize_stores

    block = _load_vectordb_config()
    stores = normalize_stores(block)

    configs = [VectorStoreConfig.from_dict(entry) if isinstance(entry, dict) else entry for entry in stores]

    if store:
        configs = [c for c in configs if c.alias == store]
        if not configs:
            error(f"No vector store configured with alias {store!r}.")
            sys.exit(1)
    return configs


def _elips_status() -> tuple[bool, str]:
    """Return ``(available, version-or-error)`` for the optional elips dependency."""
    try:
        import elips
    except ImportError as exc:
        return False, str(exc)
    return True, getattr(elips, "__version__", "unknown")


def _require_configs(store: str | None) -> list[Any]:
    """Load store configs, exiting with a hint when none are declared."""
    configs = _load_configs(store)
    if not configs:
        error("No vector stores configured.")
        dim("  Add Workspace.vectordb(stores={...}) to your workspace.py")
        sys.exit(1)
    return configs


def _discover_vector_models() -> None:
    """
    Import every module's vector models so they self-register.

    Mirrors ``Aquilary._discover_vector_models`` / ``_register_vector_models``:
    manifest-declared refs first, then a convention scan of
    ``modules/<app>/vector_models.py`` and ``modules/<app>/vector_models/``.

    Registration happens in ``VectorModelMeta``, so importing is enough.
    Failures are reported as warnings rather than raised — an inspection command
    that dies on one bad module tells the operator less than one that lists the
    rest and names the module that failed.
    """
    import importlib

    from aquilia.cli.core.workspace import ensure_importable, load_module_file, load_workspace

    ws = load_workspace()
    if not ws.exists:
        return

    ensure_importable(ws.root)

    for module_name in ws.module_names:
        manifest = ws.manifest(module_name)

        for ref in getattr(manifest, "vector_models", None) or []:
            target = ref if isinstance(ref, str) else str(getattr(ref, "class_path", ref))
            module_path = target.split(":", 1)[0]
            try:
                importlib.import_module(module_path)
            except Exception as exc:
                warning(f"{module_name}: could not import {module_path!r}: {exc}")

        module_dir = ws.module_dir(module_name)

        single = module_dir / "vector_models.py"
        if single.is_file():
            load_module_file(single, f"modules.{module_name}.vector_models")

        package = module_dir / "vector_models"
        if package.is_dir():
            for py_file in sorted(package.rglob("*.py")):
                if py_file.name.startswith("_"):
                    continue
                load_module_file(py_file, f"modules.{module_name}.vector_models.{py_file.stem}")


# ─────────────────────────────────────────────────────────────────────────────
# Group
# ─────────────────────────────────────────────────────────────────────────────


@click.group("vectordb")
def vectordb_group():
    """Inspect and maintain Aquilia vector stores."""


# ─────────────────────────────────────────────────────────────────────────────
# aq vectordb status
# ─────────────────────────────────────────────────────────────────────────────


@vectordb_group.command("status")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON")
def vectordb_status(as_json: bool):
    """
    Show configured stores and elips availability.

    Reads configuration only — no store is opened and no lock is taken, so this
    is safe to run against a directory a live server owns.
    """
    available, detail = _elips_status()
    configs = _load_configs()
    block = _load_vectordb_config()

    payload = {
        "elips": {"available": available, ("version" if available else "error"): detail},
        "enabled": bool(block.get("enabled", False)),
        "default": block.get("default", "default"),
        "stores": [c.to_dict() for c in configs],
    }

    if as_json:
        click.echo(jsonlib.dumps(payload, indent=2, default=str))
        return

    section("Vector store status")
    if available:
        success(f"elips available (version {detail})")
    else:
        warning("elips not installed — vector stores cannot open")
        dim(f"  {detail}")
        dim("  Install with: pip install 'aquilia[vectordb]'")

    if not configs:
        click.echo()
        info("No vector stores configured.")
        dim("  Add Workspace.vectordb(stores={...}) to your workspace.py")
        return

    default_alias = block.get("default", "default")
    click.echo()
    for cfg in configs:
        marker = "*" if cfg.alias == default_alias else " "
        click.echo(f" {marker} {cfg.alias}")
        dim(f"     path       {cfg.path}")
        dim(f"     dimension  {cfg.dimension}   metric {cfg.metric}   index {cfg.index}")
        dim(f"     gpu        {cfg.gpu.policy}")
        dim(f"     embedder   {cfg.embedder.provider if cfg.embedder else 'none'}")
        if cfg.read_only:
            dim("     read_only  true")
    click.echo()
    dim("* = default store")


# ─────────────────────────────────────────────────────────────────────────────
# aq vectordb gpu
# ─────────────────────────────────────────────────────────────────────────────


@vectordb_group.command("gpu")
@click.option("--store", "-s", default=None, help="Resolve policy for one store alias")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON")
def vectordb_gpu(store: str | None, as_json: bool):
    """
    Probe GPU capability and show the resolved policy per store.

    ``built`` (the elips wheel carries GPU bindings) and ``available`` (a device
    is actually present) are reported separately: a GPU-enabled build on a
    machine with no device is a normal state, and collapsing the two into one
    boolean makes that case impossible to diagnose.
    """
    available, detail = _elips_status()
    if not available:
        if as_json:
            click.echo(jsonlib.dumps({"elips": {"available": False, "error": detail}}, indent=2))
        else:
            warning("elips not installed — cannot probe GPU")
            dim(f"  {detail}")
        sys.exit(1)

    from aquilia.vectordb.gpu import probe

    info_ = probe(refresh=True)
    configs = _load_configs(store)

    if as_json:
        click.echo(
            jsonlib.dumps(
                {
                    "probe": info_.to_dict(),
                    "stores": [{"alias": c.alias, "gpu": c.gpu.to_dict()} for c in configs],
                },
                indent=2,
                default=str,
            )
        )
        return

    section("GPU capability")
    click.echo(f"  built      {info_.built}")
    click.echo(f"  available  {info_.available}")
    if info_.error:
        dim(f"  error      {info_.error}")

    if info_.devices:
        click.echo()
        for dev in info_.devices:
            click.echo(f"  [{dev.index}] {dev.name}  ({dev.backend})")
            dim(f"       memory {dev.memory_gb:.2f} GiB   fp16 {dev.supports_fp16}   unified {dev.unified_memory}")
    elif info_.built:
        click.echo()
        info("elips has GPU bindings but no usable device was detected.")

    if not configs:
        return

    click.echo()
    section("Configured policy")
    for cfg in configs:
        satisfied = cfg.gpu.policy == "cpu_only" or info_.available
        state = "ok" if satisfied else "will run on CPU"
        if cfg.gpu.policy == "require_gpu" and not info_.available:
            state = "BOOT WILL FAIL (require_gpu, no device)"
        click.echo(f"  {cfg.alias}: policy={cfg.gpu.policy} fallback={cfg.gpu.fallback} — {state}")


# ─────────────────────────────────────────────────────────────────────────────
# aq vectordb models
# ─────────────────────────────────────────────────────────────────────────────


@vectordb_group.command("models")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON")
def vectordb_models(as_json: bool):
    """
    List registered vector models and their slot routing.

    The fastest way to confirm a ``Key()`` / ``Text()`` / ``Dimension()`` marker
    landed where the author intended, since routing is resolved at class
    creation and not visible in the source.
    """
    _discover_vector_models()

    from aquilia.vectordb.registry import VectorRegistry

    rows = []
    for name, model in sorted(VectorRegistry.all_models().items()):
        schema = model._vfields
        options = model._voptions
        rows.append(
            {
                "model": f"{model.__module__}.{name}",
                "collection": options.collection,
                "store": options.store,
                "dimension": schema.dimension,
                "key": schema.key_attr,
                "text": schema.text_attr,
                "vector": schema.vector_attr,
                "payloads": sorted(schema.payloads),
                "links": sorted(getattr(model, "_vlinks", {})),
            }
        )

    if as_json:
        click.echo(jsonlib.dumps(rows, indent=2, default=str))
        return

    section("Vector models")
    if not rows:
        info("No vector models registered.")
        dim("  Declare them in modules/<app>/vector_models.py or a manifest's vector_models list.")
        return

    for row in rows:
        click.echo(f"  {row['model']}")
        dim(f"     collection {row['collection']}   store {row['store']}   dim {row['dimension']}")
        dim(f"     key={row['key']}  text={row['text']}  vector={row['vector']}")
        if row["payloads"]:
            dim(f"     payloads   {', '.join(row['payloads'])}")
        if row["links"]:
            dim(f"     links      {', '.join(row['links'])}")


# ─────────────────────────────────────────────────────────────────────────────
# aq vectordb inspect
# ─────────────────────────────────────────────────────────────────────────────


@vectordb_group.command("inspect")
@click.argument("store", required=False)
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON")
def vectordb_inspect(store: str | None, as_json: bool):
    """
    Open each store and report live health.

    Unlike ``status``, this opens the database and therefore takes the writer
    lock. elips is single-writer per directory, so this will fail while a server
    holds the same store — that is the lock working, not a bug.
    """
    result = asyncio.run(_inspect(store))

    if as_json:
        click.echo(jsonlib.dumps(result, indent=2, default=str))
        return

    section("Vector store inspection")
    for entry in result["stores"]:
        alias = entry.get("alias", "?")
        if not entry.get("ok"):
            error(f"{alias}: {entry.get('error', 'unavailable')}")
            continue
        success(f"{alias}: healthy")
        for key in ("path", "dimension", "metric", "index", "collections", "pending_writes"):
            if key in entry:
                dim(f"     {key:<15} {entry[key]}")
        gpu = entry.get("gpu") or {}
        if gpu:
            dim(f"     {'gpu':<15} built={gpu.get('built')} available={gpu.get('available')}")


async def _inspect(store: str | None) -> dict[str, Any]:
    """Open each configured store, gather health, and always close it again."""
    from aquilia.vectordb.registry import VectorRegistry

    configs = _require_configs(store)
    VectorRegistry.configure(configs)

    out: list[dict[str, Any]] = []
    try:
        for cfg in configs:
            try:
                engine = await VectorRegistry.engine(cfg.alias)
                out.append(await engine.health())
            except Exception as exc:
                out.append({"alias": cfg.alias, "ok": False, "error": str(exc)})
    finally:
        await VectorRegistry.shutdown()

    return {"stores": out}


# ─────────────────────────────────────────────────────────────────────────────
# aq vectordb compact / vacuum
# ─────────────────────────────────────────────────────────────────────────────


@vectordb_group.command("compact")
@click.argument("store", required=False)
def vectordb_compact(store: str | None):
    """
    Compact a store, reclaiming space held by deleted records.

    Takes the writer lock for the duration; run it during a maintenance window,
    not against a live serving directory.
    """
    count = asyncio.run(_maintenance(store, "compact"))
    success(f"Compacted {count} store(s).")


@vectordb_group.command("vacuum")
@click.argument("store", required=False)
def vectordb_vacuum(store: str | None):
    """Vacuum a store, releasing free pages back to the filesystem."""
    count = asyncio.run(_maintenance(store, "vacuum"))
    success(f"Vacuumed {count} store(s).")


async def _maintenance(store: str | None, action: str) -> int:
    """Run a maintenance action against every selected store."""
    from aquilia.vectordb.registry import VectorRegistry

    configs = _require_configs(store)
    VectorRegistry.configure(configs)

    done = 0
    try:
        for cfg in configs:
            if cfg.read_only:
                error(f"{cfg.alias}: store is read_only; refusing to {action}")
                sys.exit(1)
            engine = await VectorRegistry.engine(cfg.alias)
            info(f"{action} {cfg.alias} ...")
            await getattr(engine, action)()
            await engine.checkpoint()
            done += 1
    except SystemExit:
        raise
    except Exception as exc:
        error(f"{action} failed: {exc}")
        sys.exit(1)
    finally:
        await VectorRegistry.shutdown()
    return done


# ─────────────────────────────────────────────────────────────────────────────
# aq vectordb reindex
# ─────────────────────────────────────────────────────────────────────────────


@vectordb_group.command("reindex")
@click.argument("model", required=True)
@click.option("--batch-size", "-b", default=500, show_default=True, help="Rows per write batch")
def vectordb_reindex(model: str, batch_size: int):
    """
    Rebuild a mirrored collection from its SQL table.

    MODEL is the SQL model class name, e.g. ``Post``.

    This is the sanctioned repair for the bulk-write blind spot: ``bulk_create``
    and ``bulk_update`` fire no signals, so rows written that way never reach
    the mirror and the vector collection silently drifts.
    """
    count = asyncio.run(_reindex(model, batch_size))
    success(f"Reindexed {count} record(s) from {model}.")


async def _reindex(model_name: str, batch_size: int) -> int:
    """Resolve the model by name and re-run its mirror."""
    from aquilia.cli.core.workspace import load_workspace

    load_workspace()

    from aquilia.models.registry import ModelRegistry
    from aquilia.vectordb.interop import all_mirrors, reindex
    from aquilia.vectordb.registry import VectorRegistry

    model_cls = ModelRegistry.get(model_name)
    if model_cls is None:
        error(f"No SQL model named {model_name!r} is registered.")
        sys.exit(1)

    if model_cls not in all_mirrors():
        error(f"{model_name} has no @mirror registered — nothing to reindex.")
        sys.exit(1)

    VectorRegistry.configure(_require_configs(None))
    try:
        return await reindex(model_cls, batch_size=batch_size)
    except Exception as exc:
        error(f"reindex failed: {exc}")
        sys.exit(1)
    finally:
        await VectorRegistry.shutdown()


# ─────────────────────────────────────────────────────────────────────────────
# aq vectordb reembed
# ─────────────────────────────────────────────────────────────────────────────


@vectordb_group.command("reembed")
@click.option("--model", "-m", required=True, help="Vector model class name, e.g. Document")
@click.option("--to-embedder", "to_embedder", required=True, help="Target embedder URI")
@click.option("--batch-size", "-b", default=200, show_default=True, help="Records per batch")
@click.option("--dry-run", is_flag=True, default=False, help="Report what would change, write nothing")
def vectordb_reembed(model: str, to_embedder: str, batch_size: int, dry_run: bool):
    """
    Re-embed a collection under a different embedding model.

    Reads every record's stored text, embeds it with the new model, and writes
    the vector back under the same key — so keys, payloads, and any SQL links
    survive the migration.

    \b
    Two failure modes this guards against:

    * A dimension change (384 -> 1536) cannot be applied in place, because elips
      holds dimension database-global. The command refuses rather than writing
      vectors the store cannot index, and names the store to reconfigure.
    * A record with no stored text cannot be re-embedded from anything. Those
      are counted and reported rather than silently left on the old model,
      which would leave the collection split across two vector spaces.

    Example:

        aq vectordb reembed --model Document --to-embedder openai/text-embedding-3-large
    """
    result = asyncio.run(_reembed(model, to_embedder, batch_size, dry_run))

    if dry_run:
        info(f"Dry run: {result['total']} record(s) would be re-embedded with {to_embedder}.")
    else:
        success(f"Re-embedded {result['written']} record(s) with {to_embedder}.")

    if result["skipped"]:
        warning(f"{result['skipped']} record(s) had no stored text and were left unchanged.")


async def _reembed(model_name: str, to_embedder: str, batch_size: int, dry_run: bool) -> dict[str, Any]:
    """Re-embed every record of one vector model under a new embedder."""
    _discover_vector_models()

    from aquilia.vectordb.embedders import resolve_embedder
    from aquilia.vectordb.registry import VectorRegistry

    model_cls = VectorRegistry.get(model_name)
    if model_cls is None:
        error(f"No vector model named {model_name!r} is registered.")
        dim(f"  Known models: {', '.join(sorted(VectorRegistry.all_models())) or '(none)'}")
        sys.exit(1)

    schema = model_cls._vfields
    if not schema.text_attr:
        error(f"{model_name} has no text field — there is nothing to re-embed from.")
        sys.exit(1)

    configs = _require_configs(None)
    VectorRegistry.configure(configs)

    written = 0
    skipped = 0
    total = 0

    try:
        embedder = resolve_embedder(to_embedder)
        produced = await embedder.dimension()

        store = model_cls._voptions.store
        engine = await VectorRegistry.engine(store)

        if produced != engine.config.dimension:
            error(
                f"{to_embedder} produces {produced}-dimension vectors but store "
                f"{store!r} is configured for {engine.config.dimension}."
            )
            dim("  elips holds dimension database-global, so this cannot be changed in place.")
            dim(f"  Create a new store with dimension={produced} and re-ingest into it.")
            sys.exit(1)

        collection = await engine.collection(model_cls.collection_name())
        records = await engine.read(collection.sweep, include_vectors=False)
        total = len(records)

        info(f"{model_name}: {total} record(s) in collection {model_cls.collection_name()!r}")

        for start in range(0, len(records), batch_size):
            batch = records[start : start + batch_size]

            pending: list[tuple[str, str, dict[str, Any]]] = []
            for raw in batch:
                text = getattr(raw, "text", None)
                if not text:
                    skipped += 1
                    continue
                pending.append((str(raw.key), str(text), dict(raw.meta or {})))

            if not pending or dry_run:
                continue

            vectors = await embedder.embed([text for _, text, _ in pending])
            lineage = _native_lineage_for(embedder)

            payload = []
            for (key, text, meta), vector in zip(pending, vectors, strict=True):
                entry: dict[str, Any] = {"key": key, "vector": vector, "text": text, "meta": meta}
                if lineage is not None:
                    entry["lineage"] = lineage
                payload.append(entry)

            await engine.write(collection.write_many, payload)
            written += len(payload)
            info(f"  re-embedded {written}/{total}")

        if not dry_run:
            await engine.checkpoint()

    except SystemExit:
        raise
    except Exception as exc:
        error(f"reembed failed: {exc}")
        sys.exit(1)
    finally:
        await VectorRegistry.shutdown()

    return {"total": total, "written": written, "skipped": skipped}


def _native_lineage_for(embedder: Any) -> Any:
    """Build the native lineage record for a re-embedding write."""
    from aquilia.vectordb.manager import _native_lineage

    return _native_lineage(embedder)


# ─────────────────────────────────────────────────────────────────────────────
# aq vectordb compress
# ─────────────────────────────────────────────────────────────────────────────


@vectordb_group.command("compress")
@click.argument("store", required=False)
@click.option(
    "--codec",
    type=click.Choice(["pq", "opq", "sq8"], case_sensitive=False),
    default="pq",
    show_default=True,
    help="Quantization codec to train and apply",
)
@click.option("--sample-size", default=10000, show_default=True, help="Vectors sampled to train the codebook")
@click.option("--pq-dim", default=None, type=int, help="Sub-quantizer count (pq/opq)")
@click.option("--pq-bits", default=None, type=int, help="Bits per sub-quantizer code (4-8)")
@click.option("--yes", is_flag=True, default=False, help="Skip the confirmation prompt")
def vectordb_compress(
    store: str | None,
    codec: str,
    sample_size: int,
    pq_dim: int | None,
    pq_bits: int | None,
    yes: bool,
):
    """
    Train a quantization codebook and compress a store in place.

    Trades recall for memory: ``sq8`` stores one byte per dimension (~4x
    smaller), ``pq``/``opq`` store a short code per vector (~8-32x smaller).
    Distances become approximate, which is why every hit carries
    ``approximate=True`` and its codec afterwards.

    \b
    This is not reversible in place. Compression frees the full-precision
    vectors once the codebook is trained, so restoring them means re-ingesting
    or re-embedding. The confirmation prompt exists for that reason.
    """
    if not yes:
        click.confirm(
            f"Compress with {codec.lower()}? Full-precision vectors are discarded and distances become approximate.",
            abort=True,
        )

    count = asyncio.run(_compress(store, codec.lower(), sample_size, pq_dim, pq_bits))
    success(f"Compressed {count} store(s) with {codec.lower()}.")


async def _compress(
    store: str | None,
    codec: str,
    sample_size: int,
    pq_dim: int | None,
    pq_bits: int | None,
) -> int:
    """Train and apply quantization across every collection in each store."""
    from aquilia.vectordb.registry import VectorRegistry

    configs = _require_configs(store)
    VectorRegistry.configure(configs)

    done = 0
    try:
        for cfg in configs:
            if cfg.read_only:
                error(f"{cfg.alias}: store is read_only; refusing to compress")
                sys.exit(1)

            engine = await VectorRegistry.engine(cfg.alias)
            names = await engine.collection_names()

            for name in names:
                info(f"compressing {cfg.alias}/{name} with {codec} ...")
                await engine.quantize(
                    name,
                    codec=codec,
                    sample_size=sample_size,
                    pq_dim=pq_dim,
                    pq_bits=pq_bits,
                )

            await engine.checkpoint()
            done += 1
    except SystemExit:
        raise
    except Exception as exc:
        error(f"compress failed: {exc}")
        sys.exit(1)
    finally:
        await VectorRegistry.shutdown()

    return done


# ─────────────────────────────────────────────────────────────────────────────
# aq vectordb stats
# ─────────────────────────────────────────────────────────────────────────────


@vectordb_group.command("stats")
@click.argument("store", required=False)
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON")
def vectordb_stats(store: str | None, as_json: bool):
    """
    Report per-collection telemetry: record counts, tombstones, codec, WAL depth.

    Opens each store and therefore takes the writer lock, exactly as
    ``inspect`` does.
    """
    result = asyncio.run(_stats(store))

    if as_json:
        click.echo(jsonlib.dumps(result, indent=2, default=str))
        return

    section("Vector store statistics")
    for entry in result["stores"]:
        alias = entry.get("alias", "?")
        if not entry.get("ok"):
            error(f"{alias}: {entry.get('error', 'unavailable')}")
            continue

        success(f"{alias}")
        dim(f"     pending_writes  {entry.get('pending_writes')}")
        for col in entry.get("collections", []):
            click.echo(f"     {col['name']}")
            dim(
                f"        live={col.get('live')}  tombstone_ratio={col.get('tombstone_ratio')}  "
                f"dim={col.get('dimension')}  metric={col.get('metric')}  codec={col.get('codec')}"
            )


async def _stats(store: str | None) -> dict[str, Any]:
    """Gather per-collection health across the selected stores."""
    from aquilia.vectordb.registry import VectorRegistry

    configs = _require_configs(store)
    VectorRegistry.configure(configs)

    out: list[dict[str, Any]] = []
    try:
        for cfg in configs:
            try:
                engine = await VectorRegistry.engine(cfg.alias)
                out.append(await engine.stats())
            except Exception as exc:
                out.append({"alias": cfg.alias, "ok": False, "error": str(exc)})
    finally:
        await VectorRegistry.shutdown()

    return {"stores": out}
