import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { HardDrive, Cloud, Server, Shield, Layers, Zap, Box } from 'lucide-react'

export function StorageOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const features = [
    {
      icon: <Zap className="w-5 h-5 text-aquilia-400" />,
      title: 'Backend Agnostic',
      desc: 'Switch between local, S3, GCS, Azure, SFTP without changing code',
    },
    {
      icon: <Shield className="w-5 h-5 text-blue-400" />,
      title: 'Security First',
      desc: 'Path normalization, traversal protection, null byte rejection',
    },
    {
      icon: <Layers className="w-5 h-5 text-purple-400" />,
      title: 'Streaming Support',
      desc: 'Stream large files without loading into memory',
    },
    {
      icon: <Cloud className="w-5 h-5 text-cyan-400" />,
      title: 'Multi-Cloud',
      desc: 'Native support for AWS S3, Google Cloud Storage, Azure Blob',
    },
    {
      icon: <Server className="w-5 h-5 text-emerald-400" />,
      title: 'Composite Storage',
      desc: 'Route files to different backends based on rules',
    },
    {
      icon: <Box className="w-5 h-5 text-rose-400" />,
      title: 'DI Integration',
      desc: 'StorageRegistry injectable into controllers',
    },
  ]

  const backends = [
    { name: 'LocalStorage', desc: 'Store files on local filesystem', deps: 'None (stdlib)' },
    { name: 'MemoryStorage', desc: 'In-memory storage for testing', deps: 'None (stdlib)' },
    { name: 'S3Storage', desc: 'AWS S3 and S3-compatible services', deps: 'boto3' },
    { name: 'GCSStorage', desc: 'Google Cloud Storage', deps: 'google-cloud-storage' },
    { name: 'AzureBlobStorage', desc: 'Azure Blob Storage', deps: 'azure-storage-blob' },
    { name: 'SFTPStorage', desc: 'SFTP file transfer', deps: 'paramiko' },
    { name: 'CompositeStorage', desc: 'Route to multiple backends', deps: 'None' },
  ]

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <HardDrive className="w-4 h-4" />
          Storage
        </div>
        <h1 className={`text-4xl mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono">
            Storage System
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Unified async file storage abstraction with multiple backend support. Store files locally, 
          in memory, on S3, GCS, Azure Blob, SFTP, or compose multiple backends together.
        </p>
      </div>

      {/* Quick Example */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Quick Example
        </h2>

        <CodeBlock language="python">{`from aquilia.storage import StorageRegistry, LocalStorage, S3Storage

# Register backends
registry = StorageRegistry()
registry.register("local", LocalStorage(root_path="./storage"))
registry.register("s3", S3Storage(bucket="my-bucket", region="us-east-1"))
registry.set_default("local")

# Use default backend
await registry.save("file.txt", b"Hello, World!")
content = await registry.open("file.txt")

# Use specific backend
await registry.save("backup.txt", b"data", backend="s3")

# Stream large files
async with await registry.open_stream("large.mp4") as stream:
    async for chunk in stream:
        process(chunk)`}</CodeBlock>
      </section>

      {/* Features Grid */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Key Features
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {features.map((feature, i) => (
            <div
              key={i}
              className={`p-5 rounded-xl border ${isDark ? 'bg-[#111] border-white/10' : 'bg-white border-gray-200'}`}
            >
              <div className="flex items-center gap-3 mb-3">
                {feature.icon}
                <h3 className={`font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>{feature.title}</h3>
              </div>
              <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{feature.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Supported Backends */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Supported Backends
        </h2>

        <div className={`overflow-x-auto rounded-xl border ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
          <table className="w-full">
            <thead>
              <tr className={isDark ? 'bg-white/5' : 'bg-gray-50'}>
                <th className={`px-4 py-3 text-left text-sm font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Backend</th>
                <th className={`px-4 py-3 text-left text-sm font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Description</th>
                <th className={`px-4 py-3 text-left text-sm font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Dependencies</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/10' : 'divide-gray-200'}`}>
              {backends.map((backend, i) => (
                <tr key={i} className={isDark ? 'hover:bg-white/5' : 'hover:bg-gray-50'}>
                  <td className="px-4 py-3"><code className="text-aquilia-500 text-sm">{backend.name}</code></td>
                  <td className={`px-4 py-3 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{backend.desc}</td>
                  <td className={`px-4 py-3 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}><code>{backend.deps}</code></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Architecture */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Architecture
        </h2>

        <div className={`p-6 rounded-xl border font-mono text-xs ${isDark ? 'bg-[#0a0a0a] border-white/10 text-gray-300' : 'bg-gray-50 border-gray-200 text-gray-700'}`}>
          <pre className="overflow-x-auto">{`┌─────────────────────────────────────────────────────┐
│               StorageRegistry                       │
│  ┌──────────────────────────────────────────────┐  │
│  │  register(name, backend)                     │  │
│  │  get(name) -> StorageBackend                 │  │
│  │  set_default(name)                           │  │
│  │  save/open/delete (delegates to backends)    │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
  ┌─────────┐    ┌─────────┐    ┌─────────┐
  │  Local  │    │   S3    │    │   GCS   │
  │ Storage │    │ Storage │    │ Storage │
  └─────────┘    └─────────┘    └─────────┘
        │               │               │
        ▼               ▼               ▼
   Filesystem      AWS S3 API     GCS API`}</pre>
        </div>
      </section>

      {/* API Overview */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          API Overview
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          All backends implement the <code className="text-aquilia-500">StorageBackend</code> interface:
        </p>

        <CodeBlock language="python">{`class StorageBackend(ABC):
    async def save(self, path: str, content: bytes) -> None: ...
    async def open(self, path: str) -> bytes: ...
    async def delete(self, path: str) -> None: ...
    async def exists(self, path: str) -> bool: ...
    async def stat(self, path: str) -> StorageMetadata: ...
    async def listdir(self, path: str) -> list[str]: ...
    async def size(self, path: str) -> int: ...
    async def url(self, path: str, expires: int = 3600) -> str: ...`}</CodeBlock>
      </section>

      {/* Security */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Security Features
        </h2>

        <div className={`p-6 rounded-xl border ${isDark ? 'bg-[#111] border-white/10' : 'bg-white border-gray-200'}`}>
          <ul className={`space-y-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li className="flex items-start gap-2">
              <Shield className="w-4 h-4 text-aquilia-500 mt-1 shrink-0" />
              <span><strong>Path Normalization</strong> — All paths are normalized to prevent traversal attacks</span>
            </li>
            <li className="flex items-start gap-2">
              <Shield className="w-4 h-4 text-aquilia-500 mt-1 shrink-0" />
              <span><strong>Null Byte Protection</strong> — Rejects paths containing null bytes</span>
            </li>
            <li className="flex items-start gap-2">
              <Shield className="w-4 h-4 text-aquilia-500 mt-1 shrink-0" />
              <span><strong>Path Length Limits</strong> — Enforces maximum path length (default: 1024)</span>
            </li>
            <li className="flex items-start gap-2">
              <Shield className="w-4 h-4 text-aquilia-500 mt-1 shrink-0" />
              <span><strong>Safe Defaults</strong> — Secure configurations out of the box</span>
            </li>
          </ul>
        </div>

        <CodeBlock language="python">{`from aquilia.storage import StorageRegistry
from aquilia.storage.errors import PathTraversalError

registry = StorageRegistry()

# These will raise PathTraversalError:
await registry.save("../../../etc/passwd", b"data")  # Traversal attack
await registry.save("file\\x00.txt", b"data")         # Null byte injection`}</CodeBlock>
      </section>

      {/* Installation */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Installation
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The storage module is included in core Aquilia. Install additional backends as needed:
        </p>

        <CodeBlock language="bash">{`# Core storage (local, memory)
pip install aquilia

# AWS S3
pip install aquilia[s3]
# or: pip install boto3

# Google Cloud Storage
pip install aquilia[gcs]
# or: pip install google-cloud-storage

# Azure Blob Storage
pip install aquilia[azure]
# or: pip install azure-storage-blob

# SFTP
pip install aquilia[sftp]
# or: pip install paramiko

# All backends
pip install aquilia[storage]`}</CodeBlock>
      </section>

      {/* Next Steps */}
    </div>
  )
}
