import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { BookOpen, AlertTriangle } from 'lucide-react'

export function StorageAPI() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const registryMethods = [
    { method: 'register(name, backend)', desc: 'Register a storage backend' },
    { method: 'get(name)', desc: 'Get a registered backend by name' },
    { method: 'set_default(name)', desc: 'Set the default backend' },
    { method: 'save(path, content, backend=None)', desc: 'Save content to a file' },
    { method: 'open(path, backend=None)', desc: 'Read file content' },
    { method: 'delete(path, backend=None)', desc: 'Delete a file' },
    { method: 'exists(path, backend=None)', desc: 'Check if file exists' },
    { method: 'stat(path, backend=None)', desc: 'Get file metadata' },
    { method: 'listdir(path, backend=None)', desc: 'List directory contents' },
    { method: 'size(path, backend=None)', desc: 'Get file size' },
    { method: 'url(path, expires=3600, backend=None)', desc: 'Get signed URL' },
  ]

  const backendMethods = [
    { method: 'save(path, content)', desc: 'Save content to path', returns: 'None' },
    { method: 'open(path)', desc: 'Read file content', returns: 'bytes' },
    { method: 'delete(path)', desc: 'Delete file', returns: 'None' },
    { method: 'exists(path)', desc: 'Check existence', returns: 'bool' },
    { method: 'stat(path)', desc: 'Get metadata', returns: 'StorageMetadata' },
    { method: 'listdir(path)', desc: 'List directory', returns: 'list[str]' },
    { method: 'size(path)', desc: 'Get file size', returns: 'int' },
    { method: 'url(path, expires)', desc: 'Get signed URL', returns: 'str' },
  ]

  const errors = [
    { name: 'StorageError', desc: 'Base class for all storage errors' },
    { name: 'FileNotFoundError', desc: 'File does not exist' },
    { name: 'PermissionError', desc: 'No permission to access file' },
    { name: 'PathTraversalError', desc: 'Path contains ".." or null bytes' },
    { name: 'StorageBackendError', desc: 'Backend-specific error' },
    { name: 'S3Error', desc: 'AWS S3 error' },
    { name: 'GCSError', desc: 'Google Cloud Storage error' },
    { name: 'AzureError', desc: 'Azure Blob Storage error' },
  ]

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <BookOpen className="w-4 h-4" />
          Storage › API Reference
        </div>
        <h1 className={`text-4xl mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono">
            API Reference
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Complete reference for the storage system API.
        </p>
      </div>

      {/* StorageRegistry */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          StorageRegistry
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Central registry for managing multiple storage backends.
        </p>

        <CodeBlock language="python">{`class StorageRegistry:
    def __init__(self) -> None: ...
    
    def register(self, name: str, backend: StorageBackend) -> None: ...
    def get(self, name: str) -> StorageBackend: ...
    def set_default(self, name: str) -> None: ...
    
    # Convenience methods (delegate to backends)
    async def save(
        self, path: str, content: bytes, backend: str | None = None
    ) -> None: ...
    
    async def open(
        self, path: str, backend: str | None = None
    ) -> bytes: ...
    
    async def delete(
        self, path: str, backend: str | None = None
    ) -> None: ...
    
    async def exists(
        self, path: str, backend: str | None = None
    ) -> bool: ...
    
    async def stat(
        self, path: str, backend: str | None = None
    ) -> StorageMetadata: ...
    
    async def listdir(
        self, path: str, backend: str | None = None
    ) -> list[str]: ...
    
    async def size(
        self, path: str, backend: str | None = None
    ) -> int: ...
    
    async def url(
        self, path: str, expires: int = 3600, backend: str | None = None
    ) -> str: ...`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Methods</h4>
        <div className={`overflow-x-auto rounded-xl border ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={isDark ? 'bg-white/5' : 'bg-gray-50'}>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Method</th>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/10' : 'divide-gray-200'}`}>
              {registryMethods.map((m, i) => (
                <tr key={i}>
                  <td className={`px-4 py-3 ${isDark ? 'text-white' : 'text-gray-900'}`}><code>{m.method}</code></td>
                  <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{m.desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Example</h4>
        <CodeBlock language="python">{`from aquilia.storage import StorageRegistry, LocalStorage, S3Storage

registry = StorageRegistry()

# Register backends
registry.register("local", LocalStorage(root_path="./storage"))
registry.register("s3", S3Storage(bucket="my-bucket"))
registry.set_default("local")

# Use default backend
await registry.save("file.txt", b"Hello")
content = await registry.open("file.txt")

# Use specific backend
await registry.save("backup.txt", b"data", backend="s3")

# Check if file exists
if await registry.exists("file.txt"):
    metadata = await registry.stat("file.txt")
    print(f"Size: {metadata.size} bytes")`}</CodeBlock>
      </section>

      {/* StorageBackend */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          StorageBackend
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Abstract base class that all storage backends must implement.
        </p>

        <CodeBlock language="python">{`from abc import ABC, abstractmethod

class StorageBackend(ABC):
    @abstractmethod
    async def save(self, path: str, content: bytes) -> None:
        """Save content to path."""
        
    @abstractmethod
    async def open(self, path: str) -> bytes:
        """Read file content."""
        
    @abstractmethod
    async def delete(self, path: str) -> None:
        """Delete file at path."""
        
    @abstractmethod
    async def exists(self, path: str) -> bool:
        """Check if file exists."""
        
    @abstractmethod
    async def stat(self, path: str) -> StorageMetadata:
        """Get file metadata."""
        
    @abstractmethod
    async def listdir(self, path: str) -> list[str]:
        """List directory contents."""
        
    @abstractmethod
    async def size(self, path: str) -> int:
        """Get file size in bytes."""
        
    @abstractmethod
    async def url(self, path: str, expires: int = 3600) -> str:
        """Get signed URL for file access."""`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Methods</h4>
        <div className={`overflow-x-auto rounded-xl border ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={isDark ? 'bg-white/5' : 'bg-gray-50'}>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Method</th>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Description</th>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Returns</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/10' : 'divide-gray-200'}`}>
              {backendMethods.map((m, i) => (
                <tr key={i}>
                  <td className={`px-4 py-3 ${isDark ? 'text-white' : 'text-gray-900'}`}><code>{m.method}</code></td>
                  <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{m.desc}</td>
                  <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}><code className="text-aquilia-500">{m.returns}</code></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* StorageMetadata */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          StorageMetadata
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          File metadata returned by <code className="text-aquilia-500">stat()</code>.
        </p>

        <CodeBlock language="python">{`@dataclass
class StorageMetadata:
    path: str              # File path
    size: int              # Size in bytes
    content_type: str      # MIME type
    modified: datetime     # Last modified time
    etag: str | None       # ETag (if available)
    metadata: dict         # Backend-specific metadata`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Example</h4>
        <CodeBlock language="python">{`metadata = await storage.stat("document.pdf")
print(f"Size: {metadata.size} bytes")
print(f"Type: {metadata.content_type}")
print(f"Modified: {metadata.modified.isoformat()}")
print(f"ETag: {metadata.etag}")`}</CodeBlock>
      </section>

      {/* StorageFile */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          StorageFile
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Streaming file handle for large files.
        </p>

        <CodeBlock language="python">{`class StorageFile:
    async def read(self, size: int = -1) -> bytes:
        """Read up to size bytes."""
        
    async def write(self, data: bytes) -> int:
        """Write data to file."""
        
    async def seek(self, offset: int, whence: int = 0) -> int:
        """Seek to position."""
        
    async def tell(self) -> int:
        """Get current position."""
        
    async def close(self) -> None:
        """Close the file."""
        
    async def __aenter__(self) -> 'StorageFile':
        return self
        
    async def __aexit__(self, *args) -> None:
        await self.close()`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Example</h4>
        <CodeBlock language="python">{`# Stream large file
async with await storage.open_stream("large.mp4") as f:
    while True:
        chunk = await f.read(65536)  # 64KB chunks
        if not chunk:
            break
        await process(chunk)`}</CodeBlock>
      </section>

      {/* Errors */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <AlertTriangle className="inline w-6 h-6 mr-2 text-amber-500" />
          Errors
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          All storage operations raise structured exceptions.
        </p>

        <div className={`overflow-x-auto rounded-xl border ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={isDark ? 'bg-white/5' : 'bg-gray-50'}>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Exception</th>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/10' : 'divide-gray-200'}`}>
              {errors.map((e, i) => (
                <tr key={i}>
                  <td className={`px-4 py-3 ${isDark ? 'text-white' : 'text-gray-900'}`}><code>{e.name}</code></td>
                  <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{e.desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Error Handling Example</h4>
        <CodeBlock language="python">{`from aquilia.storage import (
    StorageRegistry,
    FileNotFoundError,
    PermissionError,
    PathTraversalError,
    StorageError,
)

async def safe_read(storage: StorageRegistry, path: str) -> bytes | None:
    try:
        return await storage.open(path)
    except PathTraversalError:
        logger.warning(f"Path traversal attempt: {path}")
        raise HTTPException(400, "Invalid path")
    except FileNotFoundError:
        return None
    except PermissionError:
        raise HTTPException(403, "Access denied")
    except StorageError as e:
        logger.error(f"Storage error: {e}")
        raise HTTPException(500, "Storage error")`}</CodeBlock>
      </section>
    </div>
  )
}
