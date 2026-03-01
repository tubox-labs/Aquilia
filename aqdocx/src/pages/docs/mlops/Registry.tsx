import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Brain } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function MLOpsRegistry() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Brain className="w-4 h-4" />
          MLOps / Registry
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Model Registry
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The registry provides centralized model versioning with async SQLite persistence, LRU manifest caching,
          immutability enforcement, content-addressable blob storage, and pluggable storage backends (filesystem, S3).
        </p>
      </div>

      {/* RegistryService */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>RegistryService</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Core registry service with publish/fetch/promote/delete operations and built-in integrity verification.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops.registry.service import RegistryService

registry = RegistryService(
    db_path="registry.db",       # SQLite database path
    blob_root=".aquilia-store",  # Blob storage root
    cache_size=256,              # LRU cache entries
)

# Initialize (creates tables + indexes)
await registry.initialize()

# Publish a modelpack
await registry.publish(
    name="sentiment",
    version="v2",
    archive_path="./sentiment-v2.aquilia",
)
# Steps: validate manifest → check immutability → store blobs → insert record

# Fetch a manifest (LRU-cached)
manifest = await registry.fetch("sentiment", "v2")
print(manifest.name)       # "sentiment"
print(manifest.version)    # "v2"
print(manifest.framework)  # Framework.PYTORCH

# Fetch by content digest
manifest = await registry.fetch_by_digest("sha256:abc123...")

# List all versions of a model
versions = await registry.list_versions("sentiment")
# → ["v1", "v2", "v3"]

# List all models in registry
packs = await registry.list_packs(limit=100, offset=0)

# Promote (copy tag from one version to another)
await registry.promote("sentiment", from_version="v2", to_tag="latest")

# Delete a version
await registry.delete("sentiment", "v1")

# Verify integrity (re-check all blob digests)
is_valid = await registry.verify("sentiment", "v2")
# Returns True if all blobs match their recorded SHA-256 digests`} />
      </section>

      {/* Database Schema */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Database Schema</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <code className="text-aquilia-500">RegistryDB</code> manages an async SQLite database with 3 tables and optimized indexes.
        </p>
        <CodeBlock language="sql" code={`-- Table: packs
CREATE TABLE packs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    manifest TEXT NOT NULL,          -- JSON blob
    content_digest TEXT NOT NULL,    -- SHA-256 of all blob digests
    created_at REAL NOT NULL,
    UNIQUE(name, version)
);
CREATE INDEX idx_packs_name ON packs(name);
CREATE INDEX idx_packs_digest ON packs(content_digest);

-- Table: tags
CREATE TABLE tags (
    name TEXT NOT NULL,
    tag TEXT NOT NULL,
    version TEXT NOT NULL,
    PRIMARY KEY(name, tag)
);

-- Table: blobs
CREATE TABLE blobs (
    digest TEXT PRIMARY KEY,
    size INTEGER NOT NULL,
    storage_path TEXT NOT NULL,
    ref_count INTEGER DEFAULT 1
);`} />
      </section>

      {/* Storage Backends */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Storage Backends</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Blob storage is pluggable via the <code className="text-aquilia-500">BaseStorageAdapter</code> protocol.
          Two backends are included: filesystem and S3/MinIO.
        </p>

        <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Filesystem Backend</h3>
        <CodeBlock language="python" code={`from aquilia.mlops.registry.storage.filesystem import FilesystemStorageAdapter

adapter = FilesystemStorageAdapter(root=".aquilia-blobs")

# Content-addressable layout:
# .aquilia-blobs/
# └── sha256/
#     ├── ab/
#     │   └── abc123...  ← blob file
#     └── cd/
#         └── cde456...  ← blob file

await adapter.put_blob("sha256:abc123...", data)
blob = await adapter.get_blob("sha256:abc123...")
exists = await adapter.has_blob("sha256:abc123...")
await adapter.delete_blob("sha256:abc123...")
all_digests = await adapter.list_blobs()`} />

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>S3 / MinIO Backend</h3>
        <CodeBlock language="python" code={`from aquilia.mlops.registry.storage.s3 import S3StorageAdapter

adapter = S3StorageAdapter(
    bucket="my-modelpacks",
    prefix="blobs/",
    endpoint_url="http://localhost:9000",  # MinIO
    aws_access_key_id="minioadmin",
    aws_secret_access_key="minioadmin",
    region_name="us-east-1",
)

# Same interface as filesystem
await adapter.put_blob("sha256:abc123...", data)
# → stored at s3://my-modelpacks/blobs/sha256/ab/abc123...

# Requires: pip install boto3`} />

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>Custom Backend</h3>
        <CodeBlock language="python" code={`from aquilia.mlops.registry.storage.base import BaseStorageAdapter

class MyStorageAdapter(BaseStorageAdapter):
    """Custom blob storage (GCS, Azure Blob, etc.)"""

    async def put_blob(self, digest: str, data: bytes) -> str: ...
    async def get_blob(self, digest: str) -> bytes: ...
    async def has_blob(self, digest: str) -> bool: ...
    async def delete_blob(self, digest: str) -> None: ...
    async def list_blobs(self) -> list[str]: ...`} />
      </section>

      {/* Immutability & Caching */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Immutability &amp; Caching</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className={boxClass}>
            <h4 className={`font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Immutability</h4>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Once a <code className="text-aquilia-500">name:version</code> pair is published, it cannot be overwritten.
              Attempting to publish the same name+version raises <code className="text-aquilia-500">RegistryImmutabilityFault</code>.
              This ensures reproducibility — the same version always returns the same model.
            </p>
          </div>
          <div className={boxClass}>
            <h4 className={`font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>LRU Caching</h4>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Manifest lookups are cached with an <code className="text-aquilia-500">LRUCache</code> (default 256 entries).
              Cache hits avoid SQLite queries entirely. The cache tracks hit/miss rates for monitoring.
              Cache is invalidated on publish, promote, and delete operations.
            </p>
          </div>
        </div>
      </section>

      <NextSteps
        items={[
          { text: 'Runtime Backends', link: '/docs/mlops/runtime' },
          { text: 'Serving', link: '/docs/mlops/serving' },
          { text: 'Security', link: '/docs/mlops/security' },
          { text: 'Deployment', link: '/docs/mlops/deployment' },
        ]}
      />
    </div>
  )
}
