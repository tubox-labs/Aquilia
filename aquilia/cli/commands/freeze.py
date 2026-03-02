"""Artifact freezing command.

Production-grade artifact freeze using the Aquilia Build Pipeline.

1. Runs the full build pipeline in prod mode (strict checks, LZ4 compression)
2. Generates a deterministic SHA-256 fingerprint over all Crous binaries
3. Writes a frozen manifest with integrity verification data
"""

import hashlib
import json
from pathlib import Path
from typing import Optional

from ..utils.workspace import get_workspace_file


def freeze_artifacts(
    output_dir: Optional[str] = None,
    sign: bool = False,
    verbose: bool = False,
) -> str:
    """
    Generate immutable artifacts for production.

    Uses the build pipeline in prod mode (strict validation, LZ4 compression)
    to produce verified, content-addressed Crous binary artifacts.

    Args:
        output_dir: Output directory for frozen artifacts
        sign: Sign artifacts with cryptographic signature (reserved)
        verbose: Enable verbose output

    Returns:
        Fingerprint of frozen artifacts
    """
    workspace_root = Path.cwd()
    ws_file = get_workspace_file(workspace_root)

    if not ws_file:
        raise ValueError(
            "Not in an Aquilia workspace (workspace.py not found)"
        )

    output = output_dir or str(workspace_root / 'build')
    artifacts_dir = Path(output)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # Step 1 — Production build (strict mode, compressed)
    try:
        from aquilia.build import AquiliaBuildPipeline

        result = AquiliaBuildPipeline.build(
            workspace_root=str(workspace_root),
            mode="prod",
            verbose=verbose,
            compression="lz4",
            output_dir=output,
        )

        if not result.success:
            print("\n  ✗ Freeze FAILED — cannot produce production artifacts.\n")
            for err in result.errors:
                print(f"  {err}")
            return ""

        if verbose:
            print(f"  ✓ {result.summary()}")

        fingerprint = result.fingerprint

    except ImportError:
        # Fallback to legacy compiler + manual fingerprint
        if verbose:
            print("  Build pipeline not available, falling back to legacy compiler")

        from .compile import compile_workspace
        artifacts = compile_workspace(output_dir=output, verbose=verbose)

        if verbose:
            print(f"  Compiled {len(artifacts)} artifact(s)")

        hasher = hashlib.sha256()
        for artifact_path in sorted(artifacts_dir.glob('*.crous')):
            data = artifact_path.read_bytes()
            hasher.update(data)
        fingerprint = hasher.hexdigest()

    # Step 2 — Write frozen manifest
    frozen_meta = {
        'fingerprint': fingerprint,
        'artifacts': [
            {
                'file': str(a.name),
                'size_bytes': a.stat().st_size,
                'digest': hashlib.sha256(a.read_bytes()).hexdigest(),
            }
            for a in sorted(artifacts_dir.glob('*.crous'))
        ],
        'signed': sign,
        'format': 'crous-binary',
    }

    frozen_path = artifacts_dir / 'frozen.json'
    frozen_path.write_text(json.dumps(frozen_meta, indent=2))

    if verbose:
        print(f"  Frozen manifest: {frozen_path}")
        print(f"  Fingerprint:     {fingerprint}")

    return fingerprint
