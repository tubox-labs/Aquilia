import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Brain } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function MLOpsModelpack() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Brain className="w-4 h-4" />
          MLOps / Modelpack Builder
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Modelpack Builder
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The Modelpack system provides portable, content-addressable model packaging with cryptographic integrity verification.
          Models are packaged as <code className="text-aquilia-500">.aquilia</code> TAR.GZ archives containing model files, manifest, environment lock,
          and provenance data. The system includes a content-addressable blob store, HMAC/RSA signing, and JSON Schema validation.
        </p>
      </div>

      {/* ModelpackBuilder */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>ModelpackBuilder</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          A fluent API for assembling model packages. Adds model files, environment dependencies, signatures,
          provenance metadata, and custom files into a single portable archive.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops.pack.builder import ModelpackBuilder
from aquilia.mlops import Framework, RuntimeKind, TensorSpec, DType, Provenance

builder = ModelpackBuilder(
    name="sentiment-v2",
    version="2.1.0",
    framework=Framework.PYTORCH,
    runtime=RuntimeKind.PYTHON,
)

# Add model files (computes SHA-256 digest for each)
builder.add_model("./model.pt")
builder.add_model("./tokenizer.json")

# Add extra files (config, vocab, etc.)
builder.add_file("./config.json")

# Lock environment dependencies
builder.add_env_lock("./requirements.txt")

# Input/output specifications
builder.set_inputs([
    TensorSpec(name="input_ids", shape=[1, 512], dtype=DType.INT64),
    TensorSpec(name="attention_mask", shape=[1, 512], dtype=DType.INT64),
])
builder.set_outputs([
    TensorSpec(name="logits", shape=[1, 2], dtype=DType.FLOAT32),
])

# Provenance tracking
builder.set_provenance(Provenance(
    author="ml-team",
    source="training-pipeline-v3",
    commit="abc123def",
    dataset="imdb-sentiment-v2",
    training_run_id="run-42",
))

# Custom metadata
builder.set_metadata({
    "accuracy": 0.94,
    "f1_score": 0.93,
    "training_epochs": 10,
})

# Build the archive
archive_path = builder.save(output_dir="./dist")
# → ./dist/sentiment-v2-2.1.0.aquilia`} />
      </section>

      {/* Archive Structure */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Archive Structure</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          A <code className="text-aquilia-500">.aquilia</code> archive is a standard TAR.GZ file with a well-defined internal structure.
        </p>
        <CodeBlock language="text" code={`sentiment-v2-2.1.0.aquilia (TAR.GZ)
├── manifest.json          # ModelpackManifest with blob digests
├── model/
│   ├── model.pt           # Model weights
│   └── tokenizer.json     # Tokenizer config
├── env.lock               # requirements.txt / conda.yml
├── provenance.json        # Build provenance & lineage
├── config.json            # Additional config files
└── signature.json         # Optional: HMAC or RSA signature`} />

        <div className={`${boxClass} mt-4`}>
          <h4 className={`font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Integrity Verification</h4>
          <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Every file added via <code className="text-aquilia-500">add_model()</code> gets a SHA-256 digest stored as a
            <code className="text-aquilia-500"> BlobRef</code> in the manifest. During <code className="text-aquilia-500">unpack()</code>,
            all blob digests are verified against the actual file contents. Any mismatch raises a
            <code className="text-aquilia-500"> PackIntegrityFault</code>.
          </p>
        </div>
      </section>

      {/* Unpack & Inspect */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Unpack &amp; Inspect</h2>
        <CodeBlock language="python" code={`from aquilia.mlops.pack.builder import ModelpackBuilder

# Inspect without extraction (reads manifest only)
manifest = ModelpackBuilder.inspect("./sentiment-v2-2.1.0.aquilia")
print(manifest.name)        # "sentiment-v2"
print(manifest.version)     # "2.1.0"
print(manifest.framework)   # Framework.PYTORCH
print(manifest.blobs)       # [BlobRef(digest="sha256:...", size=150000000, ...)]

# Unpack with integrity verification
ModelpackBuilder.unpack(
    "./sentiment-v2-2.1.0.aquilia",
    extract_dir="./unpacked",
)
# Verifies all blob digests → raises PackIntegrityFault on mismatch`} />
      </section>

      {/* Content Store */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Content-Addressable Store</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <code className="text-aquilia-500">ContentStore</code> provides a git-like content-addressable blob store. Files are stored
          by their SHA-256 digest in a sharded directory layout, enabling deduplication across model versions.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops.pack.content_store import ContentStore

store = ContentStore(root=".aquilia-store")

# Store a blob (content-addressable)
digest = store.put(data=model_bytes)
# Stored at: .aquilia-store/sha256/ab/abc123...

# Retrieve by digest
blob = store.get("sha256:abc123...")

# Check existence
exists = store.has("sha256:abc123...")

# Garbage collection — remove unreferenced blobs
removed = store.gc(referenced_digests={"sha256:abc123..."})

# Directory layout:
# .aquilia-store/
# └── sha256/
#     ├── ab/
#     │   └── abc123def...    ← blob file
#     └── cd/
#         └── cde456ghi...    ← blob file`} />
      </section>

      {/* Signing */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Cryptographic Signing</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">pack/signer.py</code> module provides two signing strategies:
          HMAC-SHA256 for shared secrets and RSA-PSS for asymmetric key pairs.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops.pack.signer import (
    HMACSigner, RSASigner,
    sign_archive, verify_archive,
)

# HMAC-SHA256 (shared secret)
hmac_signer = HMACSigner(secret="my-secret-key")
sig = hmac_signer.sign(data)
valid = hmac_signer.verify(data, sig)

# RSA-PSS (asymmetric)
rsa_signer = RSASigner(
    private_key_path="private.pem",
    public_key_path="public.pem",
)
sig = rsa_signer.sign(data)
valid = rsa_signer.verify(data, sig)

# Sign an entire archive
sig_path = await sign_archive("model.aquilia", hmac_signer)
# → "model.aquilia.sig"

# Verify an archive
is_valid = await verify_archive("model.aquilia", "model.aquilia.sig", hmac_signer)`} />
      </section>

      {/* Manifest Schema */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Manifest Schema Validation</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <code className="text-aquilia-500">ManifestSchema</code> validates <code className="text-aquilia-500">manifest.json</code> files
          against a JSON Schema definition. Uses a lightweight built-in validator (no external dependency).
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops.pack.manifest_schema import validate_manifest

# Validate a manifest dict against the JSON Schema
errors = validate_manifest(manifest_dict)

if errors:
    for error in errors:
        print(f"Validation error: {error}")
else:
    print("Manifest is valid")`} />
      </section>

      {/* Artifact Integration */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Aquilia Artifacts Integration</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          When <code className="text-aquilia-500">save()</code> is called, the builder also produces a <code className="text-aquilia-500">ModelArtifact</code>
          via Aquilia's artifacts system, enabling unified artifact management across the framework.
        </p>
        <CodeBlock language="python" code={`# The save() method produces both:
# 1. The .aquilia archive file
# 2. A ModelArtifact registered with FilesystemArtifactStore

# This means modelpacks appear in:
# GET /mlops/artifacts → lists all artifacts including modelpacks
# GET /mlops/artifacts/{name} → inspect a specific modelpack`} />
      </section>

      <NextSteps
        items={[
          { text: 'Registry', link: '/docs/mlops/registry' },
          { text: 'Runtime Backends', link: '/docs/mlops/runtime' },
          { text: 'Security', link: '/docs/mlops/security' },
          { text: 'MLOps Tutorial', link: '/docs/mlops/tutorial' },
        ]}
      />
    </div>
  )
}
