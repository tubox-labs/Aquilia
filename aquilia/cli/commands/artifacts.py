"""
Artifact CLI commands — aq artifacts status / verify / clean

Provides the operational surface for the Aquilia artifact subsystem:

    aq artifacts status        List all known artifacts, fingerprints, freshness
    aq artifacts verify        Recompute and check artifact integrity
    aq artifacts clean         Prune orphaned/stale artifact files

These commands close the §8.5 gap from the artifact audit: previously the
only way to check artifact integrity was a "manual step" (§3.1) noted in the
CLI output without any automated tooling to carry it out.
"""

from __future__ import annotations

import asyncio
import sys

import click


def _get_store(root: str | None = None) -> ArtifactStore:
    """Return a configured ArtifactStore."""
    from aquilia.artifacts import ArtifactStore
    from aquilia.artifacts.cache_root import resolve_artifact_root

    artifact_root = resolve_artifact_root(config_root=root)
    return ArtifactStore.for_root(artifact_root)


# ─────────────────────────────────────────────────────────────────────────────
# Group
# ─────────────────────────────────────────────────────────────────────────────


@click.group("artifacts")
def artifacts_group():
    """Manage Aquilia artifact store: status, verify, clean."""


# ─────────────────────────────────────────────────────────────────────────────
# aq artifacts status
# ─────────────────────────────────────────────────────────────────────────────


@artifacts_group.command("status")
@click.option("--root", "-r", default=None, help="Artifact root directory (default: .aquilia/artifacts)")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON")
def artifacts_status(root: str | None, as_json: bool):
    """
    List all known artifacts, their fingerprints, and freshness.

    Scans the artifact root and reports every artifact found with:
    - artifact type and key
    - schema_version and producer_version
    - fingerprint (truncated for readability)
    - created_at timestamp
    - file size
    - whether signed (HMAC)
    """
    store = _get_store(root)

    try:
        records = asyncio.run(store.status())
    except Exception as exc:
        click.secho(f"Error scanning artifact root: {exc}", fg="red", err=True)
        sys.exit(1)

    if as_json:
        import json as _json

        click.echo(_json.dumps(records, indent=2))
        return

    if not records:
        click.secho("No artifacts found in the artifact root.", fg="yellow")
        click.echo(f"Root: {store._root}")
        return

    click.secho(f"\nAquilia Artifact Store: {store._root}", bold=True)
    click.echo("─" * 70)

    for rec in records:
        artifact_type = rec.get("type", "?")
        key = rec.get("key", "?")
        fp = rec.get("fingerprint", "?")
        fp_short = fp[:16] + "..." if fp and len(fp) > 16 else fp
        schema = rec.get("schema_version", "?")
        producer = rec.get("producer_version", "?")
        created = rec.get("created_at", "?")
        size = rec.get("size", 0)
        signed = rec.get("signed", False)
        err = rec.get("error")

        if err:
            click.secho(f"  ✗ {artifact_type}/{key}", fg="red")
            click.echo(f"      Error: {err}")
        else:
            sign_badge = " 🔒" if signed else ""
            click.secho(f"  ✓ {artifact_type}/{key}{sign_badge}", fg="green")
            click.echo(f"      schema={schema}  producer={producer}")
            click.echo(f"      fingerprint={fp_short}  size={size}B  created={created}")

    click.echo()


# ─────────────────────────────────────────────────────────────────────────────
# aq artifacts verify
# ─────────────────────────────────────────────────────────────────────────────


@artifacts_group.command("verify")
@click.argument("artifact_type", required=False, default=None)
@click.option("--key", "-k", default="main", help="Artifact key (default: main)")
@click.option("--root", "-r", default=None, help="Artifact root directory")
@click.option("--all", "verify_all", is_flag=True, default=False, help="Verify all known artifact types")
def artifacts_verify(artifact_type: str | None, key: str, root: str | None, verify_all: bool):
    """
    Recompute and verify artifact fingerprint/HMAC integrity.

    Examples:

        aq artifacts verify discovery_cache
        aq artifacts verify frozen_registry --key main
        aq artifacts verify --all

    This closes the "manual step" gap in the audit (§3.1): previously operators
    had to manually inspect fingerprints; this command automates the check.
    """
    from aquilia.artifacts.registry import get_all_descriptors

    store = _get_store(root)

    if verify_all:
        types_to_check = list(get_all_descriptors().keys())
    elif artifact_type:
        types_to_check = [artifact_type]
    else:
        click.secho("Specify an artifact type or --all.", fg="yellow")
        click.echo("Known types: " + ", ".join(sorted(get_all_descriptors().keys())))
        sys.exit(1)

    all_ok = True
    for atype in types_to_check:
        ok = asyncio.run(store.verify(atype, key))
        if ok:
            click.secho(f"  ✓ {atype}/{key}: OK", fg="green")
        else:
            click.secho(f"  ✗ {atype}/{key}: FAIL (missing or corrupt)", fg="red")
            all_ok = False

    if not all_ok:
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# aq artifacts clean
# ─────────────────────────────────────────────────────────────────────────────


@artifacts_group.command("clean")
@click.option("--root", "-r", default=None, help="Artifact root directory")
@click.option("--type", "artifact_type", default=None, help="Limit to this artifact type")
@click.option("--all", "prune_all", is_flag=True, default=False, help="Remove ALL artifacts (use with caution)")
@click.option("--dry-run", is_flag=True, default=False, help="Show what would be removed without removing it")
def artifacts_clean(root: str | None, artifact_type: str | None, prune_all: bool, dry_run: bool):
    """
    Prune orphaned and stale artifact files.

    By default only removes files that don't correspond to any registered
    artifact type.  Use --all to remove all artifacts (triggering a clean
    rebuild on the next run).

    Closes the garbage-collection gap (§5.6) where discovery cache entries
    for deleted files accumulated indefinitely.
    """
    store = _get_store(root)

    if dry_run:
        click.secho("(dry-run: no files will be deleted)", fg="yellow")
        # For now, report what status shows
        records = asyncio.run(store.status())
        if not records:
            click.echo("No artifacts found.")
            return
        click.echo(f"Found {len(records)} artifact file(s).  Run without --dry-run to prune orphans.")
        return

    if prune_all:
        click.confirm(
            "This will delete ALL artifacts in the store, requiring a clean rebuild on next run. Continue?",
            abort=True,
        )
        removed = asyncio.run(store.prune(artifact_type, orphaned_only=False))
    else:
        removed = asyncio.run(store.prune(artifact_type, orphaned_only=True))

    if removed:
        click.secho(f"Removed {removed} orphaned artifact file(s).", fg="green")
    else:
        click.echo("No orphaned artifacts found.")


# ─────────────────────────────────────────────────────────────────────────────
# aq artifacts inspect (bonus: raw envelope view)
# ─────────────────────────────────────────────────────────────────────────────


@artifacts_group.command("inspect")
@click.argument("artifact_type")
@click.option("--key", "-k", default="main", help="Artifact key (default: main)")
@click.option("--root", "-r", default=None, help="Artifact root directory")
def artifacts_inspect(artifact_type: str, key: str, root: str | None):
    """
    Show the full envelope of an artifact including payload preview.
    """
    import json as _json

    store = _get_store(root)

    envelope = asyncio.run(store.get(artifact_type, key, verify_integrity=True))
    if envelope is None:
        click.secho(f"No artifact found for type={artifact_type!r} key={key!r}", fg="yellow")
        sys.exit(1)

    click.secho(f"\nArtifact: {artifact_type}/{key}", bold=True)
    click.echo("─" * 60)
    click.echo(f"  format:           {envelope.format}")
    click.echo(f"  schema_version:   {envelope.schema_version}")
    click.echo(f"  producer_version: {envelope.producer_version}")
    click.echo(f"  fingerprint:      {envelope.fingerprint}")
    click.echo(f"  signed:           {envelope.is_signed()}")
    click.echo(f"  created_at:       {envelope.created_at}")
    click.echo()
    payload_preview = _json.dumps(envelope.payload, indent=2)
    if len(payload_preview) > 2000:
        payload_preview = payload_preview[:2000] + "\n... (truncated)"
    click.echo("Payload:")
    click.echo(payload_preview)
