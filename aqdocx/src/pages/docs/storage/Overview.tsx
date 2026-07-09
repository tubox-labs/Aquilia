import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { NextSteps } from '../../../components/NextSteps'
import { HardDrive, Cloud, Shield, Layers, Zap, Cpu } from 'lucide-react'

export function StorageOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'

  const features = [
    {
      icon: <Zap className="w-5 h-5 text-aquilia-400" />,
      title: 'Backend Agnostic',
      desc: 'Switch between local filesystem, S3, GCS, Azure Blob, SFTP, and memory backends without modifying your application logic.',
    },
    {
      icon: <Shield className="w-5 h-5 text-blue-400" />,
      title: 'Security-Hardened',
      desc: 'Automatic path normalization, path traversal checks (rejects ".." segments), and null byte rejection built in.',
    },
    {
      icon: <Layers className="w-5 h-5 text-purple-400" />,
      title: 'Unified Streaming',
      desc: 'Open and stream large files via asynchronous chunk iterators, saving memory and preventing event loop blockage.',
    },
    {
      icon: <Cloud className="w-5 h-5 text-cyan-400" />,
      title: 'Composite Routing',
      desc: 'Combine multiple storage backends together under a composite manager to route files based on directories or extensions.',
    },
  ]

  const backends = [
    { name: 'LocalStorage', desc: 'Saves files directly onto the local filesystem. Supports path validation and directory auto-creation.', deps: 'None' },
    { name: 'MemoryStorage', desc: 'An ephemeral in-memory storage driver, ideal for running tests or quick processing.', deps: 'None' },
    { name: 'S3Storage', desc: 'Integrates with AWS S3 and any S3-compatible service (like MinIO or Cloudflare R2).', deps: 'boto3' },
    { name: 'GCSStorage', desc: 'Connects to Google Cloud Storage buckets using Google Cloud Credentials.', deps: 'google-cloud-storage' },
    { name: 'AzureBlobStorage', desc: 'Saves files inside Microsoft Azure Blob Storage containers.', deps: 'azure-storage-blob' },
    { name: 'SFTPStorage', desc: 'Transfers and manages files over remote servers via SSH File Transfer Protocol.', deps: 'paramiko' },
    { name: 'CompositeStorage', desc: 'Proxies multiple backends, routing write/read requests dynamically based on name filters.', deps: 'None' },
  ]

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      {/* Title Header */}
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <HardDrive className="w-4 h-4 animate-pulse" />
          Unified Storage / Overview
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          Unified Storage Subsystem
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          Aquilia provides an async-native, unified storage abstraction that decouples your file management logic from the underlying storage providers. Configure local, in-memory, or cloud backends once, and access them anywhere.
        </p>
      </div>

      {/* Quick Example */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Cpu className="w-5 h-5 text-aquilia-500" />
          Quick Example
        </h2>

        <div className="space-y-4">
          <p className={`text-sm ${subtleText}`}>
            Configure your storage integrations and interact with your files. Note that unlike legacy frameworks, you access backend instances from the registered <DocTerm id="storage.StorageRegistry">StorageRegistry</DocTerm>.
          </p>
          <CodeBlock language="python" highlightLines={[7, 8, 9, 12, 15, 16, 19, 20]}>{`from aquilia.storage import StorageRegistry
from aquilia.storage.backends import LocalStorage, S3Storage
from aquilia.storage.configs import LocalConfig, S3Config

# Setup registry and backends manually (or let Workspace do it)
registry = StorageRegistry()
registry.register("local", LocalStorage(LocalConfig(root="./storage")))
registry.register("s3", S3Storage(S3Config(bucket="my-bucket", region="us-east-1")))
registry.set_default("local")

# Save a file using the default backend (returns actual saved filename string)
saved_path = await registry.default.save("docs/invoice.pdf", b"PDF_DATA")

# Open a file as an async stream (returns a StorageFile wrapper)
async with await registry.default.open("docs/invoice.pdf") as file:
    content = await file.read()  # read all bytes
    
# Save/access from a specific non-default backend
await registry["s3"].save("backups/db.tar.gz", b"TAR_DATA")
print(await registry["s3"].exists("backups/db.tar.gz"))`}</CodeBlock>
        </div>
      </section>

      {/* Key Features */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Subsystem Features
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {features.map((feature, i) => (
            <div key={i} className="group relative overflow-hidden rounded-2xl bg-white/5 border border-white/5 hover:border-aquilia-500/20 p-6 backdrop-blur-sm transition-all duration-300 hover:translate-y-[-2px] hover:shadow-lg shadow-black/40">
              <div className="absolute top-0 bottom-0 left-0 w-1 bg-gradient-to-b from-aquilia-500 to-transparent opacity-50 group-hover:opacity-100 transition-opacity duration-300" />
              <div className="flex items-center gap-3 mb-3">
                <div className="text-aquilia-500">{feature.icon}</div>
                <h3 className={`font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>{feature.title}</h3>
              </div>
              <p className={`text-sm leading-relaxed ${subtleText}`}>{feature.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Supported Drivers */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Supported Storage Backends
        </h2>
        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="text-left py-4 px-6 font-semibold text-aquilia-500 w-44">Backend Class</th>
                <th className="text-left py-4 px-6 font-semibold">Description</th>
                <th className="text-left py-4 px-6 font-semibold w-40">Library Dependency</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {backends.map((backend, i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                  <td className="py-3.5 px-6 font-mono text-xs text-aquilia-400">
                    <DocTerm id={`storage.${backend.name}`}>{backend.name}</DocTerm>
                  </td>
                  <td className={`py-3.5 px-6 text-xs ${subtleText}`}>{backend.desc}</td>
                  <td className="py-3.5 px-6 font-mono text-xs"><code>{backend.deps}</code></td>
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
        
        {/* Floating borderless SVG Storage Architecture Flowchart */}
        <div className="w-full mx-auto py-4 flex justify-center overflow-visible">
          <svg viewBox="0 0 660 220" className="w-full h-auto overflow-visible">
            <defs>
              <linearGradient id="grad-storage-registry" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.2" />
                <stop offset="100%" stopColor="#1d4ed8" stopOpacity="0.0" />
              </linearGradient>
              <linearGradient id="grad-storage-backend" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#10b981" stopOpacity="0.2" />
                <stop offset="100%" stopColor="#047857" stopOpacity="0.0" />
              </linearGradient>
              <marker id="storage-arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 1 L 10 5 L 0 9 z" fill="#10b981" />
              </marker>
              <filter id="glow-storage" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>

            {/* Storage Registry Node */}
            <g transform="translate(230, 20)">
              <rect x="0" y="0" width="200" height="75" rx="14" fill="url(#grad-storage-registry)" stroke="#3b82f6" strokeWidth="1.5" filter="url(#glow-storage)" />
              <text x="100" y="28" textAnchor="middle" fill="#93c5fd" fontSize="12" fontWeight="700" letterSpacing="0.05em">STORAGEREGISTRY</text>
              <text x="100" y="47" textAnchor="middle" fill={isDark ? '#e5e5e5' : '#374151'} fontSize="9.5" fontFamily="monospace">registry.default</text>
              <text x="100" y="60" textAnchor="middle" fill="#60a5fa" fontSize="8.5">Routes alias to backend driver</text>
            </g>

            {/* LocalStorage Node */}
            <g transform="translate(10, 130)">
              <rect x="0" y="0" width="135" height="70" rx="12" fill="url(#grad-storage-backend)" stroke="#10b981" strokeWidth="1.5" filter="url(#glow-storage)" />
              <text x="67.5" y="27" textAnchor="middle" fill="#a7f3d0" fontSize="11" fontWeight="700" letterSpacing="0.03em">LOCALSTORAGE</text>
              <text x="67.5" y="45" textAnchor="middle" fill={isDark ? '#e5e5e5' : '#374151'} fontSize="9.5" fontFamily="monospace">root: "./uploads"</text>
              <text x="67.5" y="58" textAnchor="middle" fill="#34d399" fontSize="8">Writes to host filesystem</text>
            </g>

            {/* S3Storage Node */}
            <g transform="translate(175, 130)">
              <rect x="0" y="0" width="135" height="70" rx="12" fill="url(#grad-storage-backend)" stroke="#10b981" strokeWidth="1.5" filter="url(#glow-storage)" />
              <text x="67.5" y="27" textAnchor="middle" fill="#a7f3d0" fontSize="11" fontWeight="700" letterSpacing="0.03em">S3STORAGE</text>
              <text x="67.5" y="45" textAnchor="middle" fill={isDark ? '#e5e5e5' : '#374151'} fontSize="9.5" fontFamily="monospace">bucket: "my-bucket"</text>
              <text x="67.5" y="58" textAnchor="middle" fill="#34d399" fontSize="8">AWS S3 / R2 Cloud Object</text>
            </g>

            {/* MemoryStorage Node */}
            <g transform="translate(340, 130)">
              <rect x="0" y="0" width="135" height="70" rx="12" fill="url(#grad-storage-backend)" stroke="#10b981" strokeWidth="1.5" filter="url(#glow-storage)" />
              <text x="67.5" y="27" textAnchor="middle" fill="#a7f3d0" fontSize="11" fontWeight="700" letterSpacing="0.03em">MEMORYSTORAGE</text>
              <text x="67.5" y="45" textAnchor="middle" fill={isDark ? '#e5e5e5' : '#374151'} fontSize="9.5" fontFamily="monospace">backends: dict</text>
              <text x="67.5" y="58" textAnchor="middle" fill="#34d399" fontSize="8">Ephemeral RAM storage</text>
            </g>

            {/* SFTPStorage Node */}
            <g transform="translate(505, 130)">
              <rect x="0" y="0" width="145" height="70" rx="12" fill="url(#grad-storage-backend)" stroke="#10b981" strokeWidth="1.5" filter="url(#glow-storage)" />
              <text x="72.5" y="27" textAnchor="middle" fill="#a7f3d0" fontSize="11" fontWeight="700" letterSpacing="0.03em">SFTPSTORAGE</text>
              <text x="72.5" y="45" textAnchor="middle" fill={isDark ? '#e5e5e5' : '#374151'} fontSize="9.5" fontFamily="monospace">host: "remote.com"</text>
              <text x="72.5" y="58" textAnchor="middle" fill="#34d399" fontSize="8">Remote SSH Transfer</text>
            </g>

            {/* Connection Lines from Registry to Backends */}
            <path d="M 330 95 L 330 115 L 77 115 L 77 130" fill="none" stroke="#3b82f6" strokeWidth="1.2" strokeDasharray="3 2" markerEnd="url(#storage-arrow)" />
            <path d="M 330 95 L 330 115 L 242 115 L 242 130" fill="none" stroke="#3b82f6" strokeWidth="1.2" strokeDasharray="3 2" markerEnd="url(#storage-arrow)" />
            <path d="M 330 95 L 330 130" fill="none" stroke="#3b82f6" strokeWidth="1.2" strokeDasharray="3 2" markerEnd="url(#storage-arrow)" />
            <path d="M 330 95 L 330 115 L 577 115 L 577 130" fill="none" stroke="#3b82f6" strokeWidth="1.2" strokeDasharray="3 2" markerEnd="url(#storage-arrow)" />
          </svg>
        </div>
      </section>

      <NextSteps />
    </div>
  )
}
