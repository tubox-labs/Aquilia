import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { NextSteps } from '../../../components/NextSteps'
import { BookOpen, HardDrive, Layers, Terminal } from 'lucide-react'

export function StorageAPI() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      {/* Title Header */}
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <BookOpen className="w-4 h-4 animate-pulse" />
          Unified Storage / API Reference
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          Storage API Reference
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          Complete interface contract specifications for the unified storage registry, backend drivers, metadata structures, and async file handles.
        </p>
      </div>

      {/* Table of Contents */}
      <section className="mb-16">
        <div className="group relative overflow-hidden rounded-2xl bg-white/5 border border-white/5 p-6 backdrop-blur-sm shadow-xl">
          <div className="absolute top-0 bottom-0 left-0 w-1 bg-gradient-to-b from-aquilia-500 to-transparent opacity-50" />
          <h3 className={`font-semibold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Table of Contents</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
            {[
              { name: 'StorageRegistry Class', hash: 'storage-registry' },
              { name: 'StorageBackend Base Contract', hash: 'storage-backend' },
              { name: 'StorageFile Wrapper', hash: 'storage-file' },
              { name: 'StorageMetadata Dataclass', hash: 'storage-metadata' },
              { name: 'Storage Fault Hierarchy', hash: 'storage-faults' },
            ].map((item, i) => (
              <a key={i} href={`#${item.hash}`} className="text-aquilia-500 hover:text-aquilia-400 font-medium hover:underline flex items-center gap-1.5">
                <span className="text-aquilia-500/50">•</span> {item.name}
              </a>
            ))}
          </div>
        </div>
      </section>

      {/* StorageRegistry */}
      <section id="storage-registry" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <HardDrive className="w-5 h-5 text-aquilia-500" />
          <DocTerm id="storage.StorageRegistry">StorageRegistry</DocTerm>
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          The central coordinator for registering, retrieving, and checking the health of multiple storage backends.
        </p>

        <CodeBlock language="python">{`class StorageRegistry:
    def __init__(self) -> None:
        """Create an empty storage registry."""

    @property
    def default(self) -> StorageBackend:
        """Get the default registered StorageBackend instance.
        
        Raises StorageConfigFault if no default backend is set.
        """

    def register(self, alias: str, backend: StorageBackend) -> None:
        """Register a backend instance with the given alias name."""

    def unregister(self, alias: str) -> None:
        """Unregister a backend by its alias name."""

    def set_default(self, alias: str) -> None:
        """Define which registered alias acts as the default backend."""

    def get(self, alias: str) -> StorageBackend | None:
        """Look up a backend instance by alias. Returns None if missing."""

    def __getitem__(self, alias: str) -> StorageBackend:
        """Access a backend via bracket notation registry[alias].
        
        Raises KeyError if alias is not found.
        """

    async def initialize_all(self) -> None:
        """Run the async initialize() lifecycle hook on all registered backends."""

    async def shutdown_all(self) -> None:
        """Close/release connections on all registered backends."""

    async def health_check(self) -> dict[str, bool]:
        """Runs a ping() check on each registered backend.
        
        Returns a dictionary of {alias: is_healthy}.
        """`}</CodeBlock>
      </section>

      {/* StorageBackend */}
      <section id="storage-backend" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-500" />
          <DocTerm id="storage.StorageBackend">StorageBackend</DocTerm>
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Abstract Base Class establishing the contract all storage drivers (Local, S3, Memory, GCS, SFTP) must implement.
        </p>

        <CodeBlock language="python">{`from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import BinaryIO

class StorageBackend(ABC):
    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Returns the driver name identifier (e.g. 'local', 's3')."""

    async def initialize(self) -> None:
        """Bootstrap directory structures, connections, or credential handshakes."""

    async def ping(self) -> bool:
        """Verifies driver accessibility. Returns True if healthy, False otherwise."""

    @abstractmethod
    async def save(
        self,
        name: str,
        content: bytes | BinaryIO | AsyncIterator[bytes] | StorageFile,
        *,
        content_type: str | None = None,
        metadata: dict[str, str] | None = None,
        overwrite: bool = False,
    ) -> str:
        """Save a file to the backend.
        
        Args:
            name: Path/key target.
            content: Raw byte content, file-like object, or async generator.
            content_type: MIME string (auto-detected if None).
            metadata: Custom tag key/values.
            overwrite: Replaces the file if True, otherwise appends an increments counter.

        Returns:
            The final saved relative path string.
        """

    @abstractmethod
    async def open(self, name: str, mode: str = "rb") -> StorageFile:
        """Open a file handle for reading or writing.
        
        Returns:
            A StorageFile wrapper.
        """

    @abstractmethod
    async def delete(self, name: str) -> None:
        """Deletes a file. Idempotent: does NOT raise if the file does not exist."""

    @abstractmethod
    async def exists(self, name: str) -> bool:
        """Returns True if the file exists, False otherwise."""

    @abstractmethod
    async def stat(self, name: str) -> StorageMetadata:
        """Returns metadata for the file. Raises FileNotFoundError if missing."""

    @abstractmethod
    async def listdir(self, path: str = "") -> tuple[list[str], list[str]]:
        """List subdirectories and files in a path.
        
        Returns:
            A tuple of (directories_list, files_list).
        """

    @abstractmethod
    async def size(self, name: str) -> int:
        """Returns the file size in bytes."""

    @abstractmethod
    async def url(self, name: str, expire: int | None = None) -> str:
        """Generates a public URL or signed temporary URL.
        
        Args:
            expire: URL expiration period in seconds.
        """`}</CodeBlock>
      </section>

      {/* StorageFile */}
      <section id="storage-file" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-500" />
          <DocTerm id="storage.StorageFile">StorageFile</DocTerm>
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          An asynchronous wrapper for reading and writing files. Implements the async context manager and iterator protocols.
        </p>

        <CodeBlock language="python">{`class StorageFile:
    @property
    def closed(self) -> bool:
        """Returns True if the file has been closed."""

    async def read(self, size: int = -1) -> bytes:
        """Read up to size bytes. If -1, reads the entire file."""

    async def write(self, data: bytes) -> int:
        """Write bytes to the file (requires a writable open mode)."""

    async def seek(self, offset: int, whence: int = 0) -> int:
        """Change the stream position relative to start (0), current (1), or end (2)."""

    async def tell(self) -> int:
        """Return the current stream position."""

    async def close(self) -> None:
        """Release underlying system handles or HTTP connections."""

    async def chunks(self, chunk_size: int = 65536) -> AsyncIterator[bytes]:
        """Stream the file in custom-sized byte chunks."""`}</CodeBlock>
      </section>

      {/* StorageMetadata */}
      <section id="storage-metadata" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-500" />
          <DocTerm id="storage.StorageMetadata">StorageMetadata</DocTerm>
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          An immutable dataclass containing metadata for a stored file, returned by backend stat calls.
        </p>

        <CodeBlock language="python">{`@dataclass(frozen=True)
class StorageMetadata:
    name: str                           # Relative path key
    size: int = 0                       # Size in bytes
    content_type: str = "application/octet-stream"
    etag: str = ""                      # SHA-256 or remote MD5 hash
    last_modified: datetime | None = None
    created_at: datetime | None = None
    metadata: dict[str, str] = field(default_factory=dict)
    storage_class: str = ""             # e.g., "STANDARD", "GLACIER"

    def to_dict(self) -> dict[str, Any]:
        """Convert metadata values to a serialized dictionary."""`}</CodeBlock>
      </section>

      {/* Storage Faults */}
      <section id="storage-faults" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Terminal className="w-5 h-5 text-aquilia-500" />
          Storage Fault Hierarchy
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Errors thrown by storage providers are normalized under the <code className="text-aquilia-500">"storage"</code> fault domain.
        </p>

        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="text-left py-4 px-6 font-semibold text-aquilia-500 w-52">Fault Class</th>
                <th className="text-left py-4 px-6 font-semibold">Fault Code</th>
                <th className="text-left py-4 px-6">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['StorageError', 'STORAGE_ERROR', 'Base class for all storage failures.'],
                ['FileNotFoundError', 'STORAGE_FILE_NOT_FOUND', 'Raised when reading, deleting, or statting a missing file.'],
                ['PermissionError', 'STORAGE_PERMISSION_DENIED', 'Raised when lacking local file access permissions or cloud bucket policies.'],
                ['StorageFullError', 'STORAGE_FULL', 'Raised when local storage quota or bucket limits are exceeded.'],
                ['BackendUnavailableError', 'STORAGE_BACKEND_UNAVAILABLE', 'Raised when remote services (S3/Azure/SFTP) are offline.'],
                ['StorageIOFault', 'STORAGE_IO_ERROR', 'Raised when performing operations on closed files or wrong read/write modes.'],
                ['StorageConfigFault', 'STORAGE_CONFIG_ERROR', 'Raised on incorrect backend parameters or missing registry configurations.'],
              ].map(([fault, code, desc], i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                  <td className="py-3.5 px-6 font-mono text-xs font-semibold text-aquilia-400">{fault}</td>
                  <td className="py-3.5 px-6 font-mono text-xs text-aquilia-500">{code}</td>
                  <td className={`py-3.5 px-6 text-xs ${subtleText}`}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <NextSteps />
    </div>
  )
}
