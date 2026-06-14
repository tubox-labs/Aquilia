# aq freeze

Freeze compiled artifacts into an integrity snapshot for production deployments. Generates a deterministic SHA-256 inventory with optional cryptographic signing.

## Usage

```bash
aq freeze [OPTIONS]
```

## Options

| Option     | Description                                   | Default       |
| ---------- | --------------------------------------------- | ------------- |
| `--output` | Output directory for frozen artifacts         | `artifacts/`  |
| `--sign`   | Sign artifacts with cryptographic signature   | `False`       |

## Process

1. **Compile** — Runs `aq compile` to generate `.surp` artifacts
2. **Hash** — Computes SHA-256 digest for each artifact file
3. **Aggregate** — Generates a combined fingerprint from all hashes
4. **Write** — Creates `frozen.surp` manifest containing:
   - Combined fingerprint
   - Per-file digests and sizes
   - Signing status
   - Artifact format metadata

## Frozen Manifest Structure

```json
{
  "fingerprint": "a1b2c3d4e5f6...",
  "artifacts": [
    {
      "file": "routes.surp",
      "size_bytes": 1234,
      "digest": "sha256:..."
    },
    {
      "file": "di_graph.surp",
      "size_bytes": 5678,
      "digest": "sha256:..."
    }
  ],
  "signed": false,
  "format": "surp-artifact-snapshot"
}
```

## Use Cases

- **CI/CD integrity checks** — verify frozen artifacts match deployed versions
- **Deployment validation** — ensure artifacts haven't been tampered with
- **Rollback safety** — reference known-good artifact snapshots

!!! note "Signing"
    The `--sign` flag is reserved for future cryptographic signing support. Currently it sets the `signed` metadata field without applying actual cryptographic signatures.

## Examples

```bash
# Freeze artifacts to default directory
aq freeze

# Freeze to custom output directory
aq freeze --output=dist/

# Freeze with signing metadata
aq freeze --sign

# Compile first, then freeze
aq compile && aq freeze
```

## See Also

- [`aq compile`](compile.md) — Compile manifests to artifacts
- [`aq artifacts`](artifacts.md) — Artifact management commands
- [`aq deploy`](deploy.md) — Generate deployment files