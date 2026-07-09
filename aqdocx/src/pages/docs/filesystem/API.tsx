import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { NextSteps } from '../../../components/NextSteps'
import { BookOpen, FileText, Layers, Terminal } from 'lucide-react'

export function FilesystemAPI() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      {/* Title Header */}
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <BookOpen className="w-4 h-4 animate-pulse" />
          Filesystem / API Reference
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          Filesystem API Reference
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          Detailed interface specifications for standalone async file operations, context-managed file handles, and directory path wrappers.
        </p>
      </div>

      {/* Table of Contents */}
      <section className="mb-16">
        <div className="group relative overflow-hidden rounded-2xl bg-white/5 border border-white/5 p-6 backdrop-blur-sm shadow-xl">
          <div className="absolute top-0 bottom-0 left-0 w-1 bg-gradient-to-b from-aquilia-500 to-transparent opacity-50" />
          <h3 className={`font-semibold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Table of Contents</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
            {[
              { name: 'Core Helper Functions', hash: 'helper-functions' },
              { name: 'FileSystem Service', hash: 'filesystem-service' },
              { name: 'AsyncFile Handle', hash: 'async-file' },
              { name: 'AsyncPath Wrapper', hash: 'async-path' },
              { name: 'Filesystem Fault Hierarchy', hash: 'fs-faults' },
            ].map((item, i) => (
              <a key={i} href={`#${item.hash}`} className="text-aquilia-500 hover:text-aquilia-400 font-medium hover:underline flex items-center gap-1.5">
                <span className="text-aquilia-500/50">•</span> {item.name}
              </a>
            ))}
          </div>
        </div>
      </section>

      {/* Helper Functions */}
      <section id="helper-functions" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <FileText className="w-5 h-5 text-aquilia-500" />
          Core Helper Functions
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          High-level standalone functions available directly under <code className="text-aquilia-500">aquilia.filesystem</code>.
        </p>

        <CodeBlock language="python">{`from aquilia.filesystem import async_open, read_file, write_file

async def async_open(
    path: str | Path,
    mode: str = "r",
    encoding: str | None = None,
    errors: str | None = None,
    buffering: int = -1,
    newline: str | None = None,
) -> AsyncFile:
    """Opens a file asynchronously. Yields an AsyncFile context manager."""

async def read_file(
    path: str | Path,
    encoding: str = "utf-8",
    errors: str = "strict",
) -> str | bytes:
    """Read and return entire file content. Returns bytes if binary mode is requested."""

async def write_file(
    path: str | Path,
    data: str | bytes,
    encoding: str = "utf-8",
    errors: str = "strict",
    atomic: bool = True,           # Uses temp file + rename if True
    make_parents: bool = True,     # Auto-creates parent directories
) -> None:
    """Writes content to a file."""

async def append_file(
    path: str | Path,
    data: str | bytes,
    encoding: str = "utf-8",
    errors: str = "strict",
) -> None:
    """Appends data to the end of a file."""

async def copy_file(src: str | Path, dst: str | Path) -> None:
    """Copy a file from source to destination."""

async def move_file(src: str | Path, dst: str | Path) -> None:
    """Move/rename a file atomically."""

async def delete_file(path: str | Path) -> None:
    """Delete a file. Idempotent: does NOT raise if file is missing."""

async def file_exists(path: str | Path) -> bool:
    """Returns True if the path exists and is a file."""

async def file_stat(path: str | Path) -> os.stat_result:
    """Retrieve file metadata (size, last modified time, etc.)."""`}</CodeBlock>
      </section>

      {/* FileSystem Service */}
      <section id="filesystem-service" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-500" />
          <DocTerm id="filesystem.FileSystem">FileSystem</DocTerm>
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          The DI-managed filesystem service class containing all query and operation methods.
        </p>

        <CodeBlock language="python">{`class FileSystem:
    def __init__(self, config: FileSystemConfig | None = None) -> None:
        """Create a new FileSystem service wrapper."""

    async def open(self, path: str | Path, mode: str = "r", **kwargs: Any) -> AsyncFile:
        """Alias for async_open."""

    async def read(self, path: str | Path, **kwargs: Any) -> str | bytes:
        """Alias for read_file."""

    async def write(self, path: str | Path, data: str | bytes, **kwargs: Any) -> None:
        """Alias for write_file."""

    async def list_dir(self, path: str | Path) -> list[str]:
        """List all filenames and subdirectories in a directory path."""

    async def scan_dir(self, path: str | Path) -> AsyncIterator[DirEntry]:
        """Asynchronously iterate over entries (files/directories) in a path."""

    async def make_dir(self, path: str | Path, parents: bool = True, exist_ok: bool = True) -> None:
        """Create a new directory."""

    async def remove_dir(self, path: str | Path) -> None:
        """Remove an empty directory."""

    async def remove_tree(self, path: str | Path) -> None:
        """Delete a directory and all of its contents recursively."""

    async def copy_tree(self, src: str | Path, dst: str | Path) -> None:
        """Copy a directory tree recursively to another destination."""

    def walk(
        self,
        top: str | Path,
        top_down: bool = True,
        on_error: Callable[[OSError], Any] | None = None,
        follow_symlinks: bool = False,
    ) -> AsyncIterator[tuple[str, list[str], list[str]]]:
        """Asynchronously walk a directory tree yielding (dirpath, dirnames, filenames)."""`}</CodeBlock>
      </section>

      {/* AsyncFile */}
      <section id="async-file" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-500" />
          <DocTerm id="filesystem.AsyncFile">AsyncFile</DocTerm>
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          An asynchronous file handle wrapping a native file object, offering non-blocking reads and writes.
        </p>

        <CodeBlock language="python">{`class AsyncFile:
    @property
    def name(self) -> str:
        """The file path."""

    @property
    def mode(self) -> str:
        """The open mode."""

    @property
    def closed(self) -> bool:
        """Returns True if the file has been closed."""

    @property
    def encoding(self) -> str | None:
        """File encoding (None for binary files)."""

    async def read(self, size: int = -1) -> bytes | str:
        """Read up to size bytes/characters. Reads all if size=-1."""

    async def readline(self) -> bytes | str:
        """Read a single line."""

    async def readlines(self) -> list[bytes | str]:
        """Read all lines into a list."""

    async def readinto(self, buffer: bytearray) -> int:
        """Read bytes into a pre-allocated buffer (binary mode only)."""

    async def write(self, data: bytes | str) -> int:
        """Write data to the file."""

    async def writelines(self, lines: Iterable[bytes | str]) -> None:
        """Write an iterable of lines."""

    async def seek(self, offset: int, whence: int = 0) -> int:
        """Change the stream position."""

    async def tell(self) -> int:
        """Return the current stream position."""

    async def truncate(self, size: int | None = None) -> int:
        """Truncate the file to at most size bytes."""

    async def flush(self) -> None:
        """Flush write buffer to disk."""

    async def close(self) -> None:
        """Flush write buffers and close the file handle."""`}</CodeBlock>
      </section>

      {/* AsyncPath */}
      <section id="async-path" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-500" />
          <DocTerm id="filesystem.AsyncPath">AsyncPath</DocTerm>
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          An asynchronous object-oriented path class wrapper providing pathlib-style methods.
        </p>

        <CodeBlock language="python">{`class AsyncPath:
    def __init__(self, *args: str | Path | AsyncPath, **kwargs: Any) -> None

    @property
    def name(self) -> str: ...
    @property
    def stem(self) -> str: ...
    @property
    def suffix(self) -> str: ...
    @property
    def parent(self) -> AsyncPath: ...

    async def exists(self) -> bool: ...
    async def is_file(self) -> bool: ...
    async def is_dir(self) -> bool: ...
    async def stat(self) -> os.stat_result: ...
    async def mkdir(self, parents: bool = True, exist_ok: bool = True) -> None: ...
    async def rmdir(self) -> None: ...
    async def unlink(self, missing_ok: bool = False) -> None: ...
    async def open(self, mode: str = "r", **kwargs: Any) -> AsyncFile: ...
    async def read_text(self, encoding: str = "utf-8") -> str: ...
    async def write_text(self, data: str, encoding: str = "utf-8") -> None: ...
    async def read_bytes(self) -> bytes: ...
    async def write_bytes(self, data: bytes) -> None: ...`}</CodeBlock>
      </section>

      {/* Errors */}
      <section id="fs-faults" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Terminal className="w-5 h-5 text-aquilia-500" />
          Filesystem Fault Hierarchy
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Exception faults raised by the async filesystem module under the <code className="text-aquilia-500">io</code> domain.
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
                ['FileSystemFault', 'FILESYSTEM_ERROR', 'Base class for all filesystem faults.'],
                ['FileNotFoundFault', 'FS_NOT_FOUND', 'Raised when a file or directory does not exist.'],
                ['PermissionDeniedFault', 'FS_PERMISSION_DENIED', 'Raised when the process lacks permission.'],
                ['FileExistsFault', 'FS_ALREADY_EXISTS', 'Raised when a file exists and overwrite=False.'],
                ['IsDirectoryFault', 'FS_IS_DIRECTORY', 'Raised when file operations target a directory.'],
                ['NotDirectoryFault', 'FS_NOT_DIRECTORY', 'Raised when directory operations target a file.'],
                ['DiskFullFault', 'FS_DISK_FULL', 'Raised when no space is left on the device.'],
                ['PathTraversalFault', 'FS_PATH_TRAVERSAL', 'Raised when path traversal attacks (..) are blocked.'],
                ['PathTooLongFault', 'FS_PATH_TOO_LONG', 'Raised when a path exceeds length limits.'],
                ['FileSystemIOFault', 'FS_IO_ERROR', 'Raised on general unclassified OS I/O failures.'],
                ['FileClosedFault', 'FS_FILE_CLOSED', 'Raised when performing operations on closed handles.'],
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
