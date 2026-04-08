import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { BookOpen, AlertTriangle } from 'lucide-react'

export function FilesystemAPI() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const asyncOpenParams = [
    { name: 'path', type: 'str | Path', def: '—', desc: 'Path to the file. Validated for security.' },
    { name: 'mode', type: 'str', def: '"r"', desc: 'File open mode. r=read, w=write, a=append, b=binary, +=read/write.' },
    { name: 'encoding', type: 'str | None', def: 'None', desc: 'Text encoding. Defaults to UTF-8 for text modes, None for binary.' },
    { name: 'errors', type: 'str | None', def: 'None', desc: 'How to handle encoding errors: strict, ignore, replace.' },
    { name: 'buffering', type: 'int', def: '-1', desc: 'Buffer size. -1=system default, 0=unbuffered, 1=line buffered.' },
    { name: 'newline', type: 'str | None', def: 'None', desc: 'Line ending mode. None=universal, ""=no translation, "\\n"=Unix.' },
  ]

  const asyncOpenRaises = [
    { exc: 'FileNotFoundFault', when: "File doesn't exist (read modes)" },
    { exc: 'PermissionDeniedFault', when: 'No read/write permission' },
    { exc: 'PathTraversalFault', when: 'Path contains ".." or null bytes' },
    { exc: 'IsDirectoryFault', when: 'Path is a directory, not a file' },
  ]

  const writeFileParams = [
    { name: 'path', type: 'str | Path', def: '—', desc: "Destination path. Created if doesn't exist." },
    { name: 'data', type: 'str | bytes', def: '—', desc: 'Content to write. Type determines binary/text mode.' },
    { name: 'encoding', type: 'str', def: '"utf-8"', desc: 'Encoding for str data.' },
    { name: 'atomic', type: 'bool', def: 'True', desc: 'If True, writes to temp file then renames. Prevents partial writes.' },
    { name: 'make_parents', type: 'bool', def: 'True', desc: "Create parent directories if they don't exist." },
  ]

  const errors = [
    { name: 'FileSystemFault', code: 'FILESYSTEM_ERROR', desc: 'Base class for all filesystem errors' },
    { name: 'FileNotFoundFault', code: 'FILE_NOT_FOUND', desc: 'File or directory does not exist' },
    { name: 'PermissionDeniedFault', code: 'PERMISSION_DENIED', desc: 'No permission to read/write/execute' },
    { name: 'FileExistsFault', code: 'FILE_EXISTS', desc: 'File already exists (when overwrite=False)' },
    { name: 'IsDirectoryFault', code: 'IS_DIRECTORY', desc: 'Expected file but found directory' },
    { name: 'NotDirectoryFault', code: 'NOT_DIRECTORY', desc: 'Expected directory but found file' },
    { name: 'DiskFullFault', code: 'DISK_FULL', desc: 'No space left on device' },
    { name: 'PathTraversalFault', code: 'PATH_TRAVERSAL', desc: 'Path contains ".." or null bytes' },
    { name: 'PathTooLongFault', code: 'PATH_TOO_LONG', desc: 'Path exceeds maximum length' },
    { name: 'FileSystemIOFault', code: 'FILESYSTEM_IO', desc: 'General I/O error' },
    { name: 'FileClosedFault', code: 'FILE_CLOSED', desc: 'Operation on closed file handle' },
  ]

  const toc = [
    { label: 'async_open', anchor: '#async_open' },
    { label: 'read_file', anchor: '#read_file' },
    { label: 'write_file', anchor: '#write_file' },
    { label: 'append_file', anchor: '#append_file' },
    { label: 'copy_file', anchor: '#copy_file' },
    { label: 'move_file', anchor: '#move_file' },
    { label: 'delete_file', anchor: '#delete_file' },
    { label: 'file_exists', anchor: '#file_exists' },
    { label: 'file_stat', anchor: '#file_stat' },
    { label: 'AsyncFile', anchor: '#asyncfile' },
    { label: 'FileSystem', anchor: '#filesystem' },
    { label: 'AsyncPath', anchor: '#asyncpath' },
    { label: 'Security Functions', anchor: '#security' },
    { label: 'Errors', anchor: '#errors' },
  ]

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <BookOpen className="w-4 h-4" />
          Filesystem › API Reference
        </div>
        <h1 className={`text-4xl mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono">
            API Reference
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Complete reference for all filesystem operations, classes, and types.
        </p>
      </div>

      {/* Table of Contents */}
      <section className="mb-12">
        <div className={`p-6 rounded-xl border ${isDark ? 'bg-[#111] border-white/10' : 'bg-white border-gray-200'}`}>
          <h3 className={`font-semibold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Contents</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {toc.map((item, i) => (
              <a key={i} href={item.anchor} className="text-aquilia-500 hover:text-aquilia-400 text-sm">{item.label}</a>
            ))}
          </div>
        </div>
      </section>

      {/* async_open */}
      <section id="async_open" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          async_open
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Opens a file asynchronously and returns an <code className="text-aquilia-500">AsyncFile</code> context manager.
        </p>

        <CodeBlock language="python">{`async def async_open(
    path: str | Path,             # Path to the file
    mode: str = "r",              # File mode: r, w, a, rb, wb, ab, r+, w+, a+
    encoding: str | None = None,  # Text encoding (default: utf-8 for text modes)
    errors: str | None = None,    # Encoding error handling
    buffering: int = -1,          # Buffer size (-1 = default)
    newline: str | None = None,   # Line ending mode
) -> AsyncFile: ...`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Parameters</h4>
        <div className={`overflow-x-auto rounded-xl border ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={isDark ? 'bg-white/5' : 'bg-gray-50'}>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Name</th>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Type</th>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Default</th>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/10' : 'divide-gray-200'}`}>
              {asyncOpenParams.map((p, i) => (
                <tr key={i}>
                  <td className={`px-4 py-3 ${isDark ? 'text-white' : 'text-gray-900'}`}><code>{p.name}</code></td>
                  <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}><code className="text-aquilia-500">{p.type}</code></td>
                  <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}><code>{p.def}</code></td>
                  <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{p.desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Returns</h4>
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <code className="text-aquilia-500">AsyncFile</code> — An async context manager wrapping the file handle.
        </p>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Raises</h4>
        <div className={`overflow-x-auto rounded-xl border ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={isDark ? 'bg-white/5' : 'bg-gray-50'}>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Exception</th>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>When</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/10' : 'divide-gray-200'}`}>
              {asyncOpenRaises.map((r, i) => (
                <tr key={i}>
                  <td className={`px-4 py-3 ${isDark ? 'text-white' : 'text-gray-900'}`}><code>{r.exc}</code></td>
                  <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{r.when}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Example</h4>
        <CodeBlock language="python">{`from aquilia.filesystem import async_open

# Text file reading
async with await async_open("data.txt", "r") as f:
    content = await f.read()

# Binary file writing
async with await async_open("image.png", "wb") as f:
    await f.write(image_bytes)

# Line-by-line iteration
async with await async_open("log.txt", "r") as f:
    async for line in f:
        print(line.strip())`}</CodeBlock>
      </section>

      {/* read_file */}
      <section id="read_file" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          read_file
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Reads an entire file into memory as string or bytes.
        </p>

        <CodeBlock language="python">{`async def read_file(
    path: str | Path,             # Path to the file
    mode: Literal["t", "b"] = "t",  # "t" = text (str), "b" = binary (bytes)
    encoding: str = "utf-8",      # Text encoding (text mode only)
) -> str | bytes: ...`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Example</h4>
        <CodeBlock language="python">{`from aquilia.filesystem import read_file

# Read as text (default)
content = await read_file("config.json")
config = json.loads(content)

# Read as bytes
image_data = await read_file("logo.png", mode="b")

# Specify encoding
latin_text = await read_file("legacy.txt", encoding="latin-1")`}</CodeBlock>
      </section>

      {/* write_file */}
      <section id="write_file" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          write_file
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Writes data to a file. Uses atomic writes by default to prevent corruption.
        </p>

        <CodeBlock language="python">{`async def write_file(
    path: str | Path,             # Path to the file
    data: str | bytes,            # Content to write
    encoding: str = "utf-8",      # Text encoding (for str data)
    atomic: bool = True,          # Use atomic write (temp + rename)
    make_parents: bool = True,    # Create parent directories if needed
) -> None: ...`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Parameters</h4>
        <div className={`overflow-x-auto rounded-xl border ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={isDark ? 'bg-white/5' : 'bg-gray-50'}>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Name</th>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Type</th>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Default</th>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/10' : 'divide-gray-200'}`}>
              {writeFileParams.map((p, i) => (
                <tr key={i}>
                  <td className={`px-4 py-3 ${isDark ? 'text-white' : 'text-gray-900'}`}><code>{p.name}</code></td>
                  <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}><code className="text-aquilia-500">{p.type}</code></td>
                  <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}><code>{p.def}</code></td>
                  <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{p.desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Example</h4>
        <CodeBlock language="python">{`from aquilia.filesystem import write_file
import json

# Write text (atomic by default)
await write_file("config.json", json.dumps(config, indent=2))

# Write binary
await write_file("image.png", image_bytes)

# Disable atomic for log files (append is more common)
await write_file("debug.log", log_line, atomic=False)

# Will create parent directories
await write_file("output/reports/2024/report.json", data)`}</CodeBlock>
      </section>

      {/* append_file */}
      <section id="append_file" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          append_file
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Appends data to the end of a file. Creates the file if it doesn't exist.
        </p>

        <CodeBlock language="python">{`async def append_file(
    path: str | Path,             # Path to the file
    data: str | bytes,            # Content to append
    encoding: str = "utf-8",      # Text encoding (for str data)
    make_parents: bool = True,    # Create parent directories if needed
) -> None: ...`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Example</h4>
        <CodeBlock language="python">{`from aquilia.filesystem import append_file
from datetime import datetime

# Append log entry
await append_file(
    "app.log",
    f"[{datetime.now().isoformat()}] User logged in\\n"
)

# Append binary data
await append_file("data.bin", new_chunk)`}</CodeBlock>
      </section>

      {/* copy_file */}
      <section id="copy_file" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          copy_file
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Copies a file from source to destination.
        </p>

        <CodeBlock language="python">{`async def copy_file(
    src: str | Path,              # Source file path
    dst: str | Path,              # Destination path
    overwrite: bool = False,      # Overwrite if destination exists
    preserve_metadata: bool = True,  # Preserve mtime, mode
) -> None: ...`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Example</h4>
        <CodeBlock language="python">{`from aquilia.filesystem import copy_file

# Basic copy
await copy_file("original.txt", "backup.txt")

# Overwrite existing
await copy_file("new_config.json", "config.json", overwrite=True)

# Don't preserve metadata
await copy_file("source.py", "dest.py", preserve_metadata=False)`}</CodeBlock>
      </section>

      {/* move_file */}
      <section id="move_file" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          move_file
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Moves or renames a file. Works across filesystems.
        </p>

        <CodeBlock language="python">{`async def move_file(
    src: str | Path,              # Source file path
    dst: str | Path,              # Destination path
    overwrite: bool = False,      # Overwrite if destination exists
) -> None: ...`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Example</h4>
        <CodeBlock language="python">{`from aquilia.filesystem import move_file

# Rename
await move_file("draft.txt", "final.txt")

# Move to different directory
await move_file("uploads/temp.jpg", "storage/images/photo.jpg")

# Move with overwrite
await move_file("new.json", "config.json", overwrite=True)`}</CodeBlock>
      </section>

      {/* delete_file */}
      <section id="delete_file" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          delete_file
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Deletes a file.
        </p>

        <CodeBlock language="python">{`async def delete_file(
    path: str | Path,             # Path to the file
    missing_ok: bool = False,     # Don't raise if file doesn't exist
) -> None: ...`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Example</h4>
        <CodeBlock language="python">{`from aquilia.filesystem import delete_file

# Delete file
await delete_file("temp.txt")

# Delete if exists (no error if missing)
await delete_file("maybe_exists.txt", missing_ok=True)`}</CodeBlock>
      </section>

      {/* file_exists */}
      <section id="file_exists" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          file_exists
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Checks if a path exists and is a file.
        </p>

        <CodeBlock language="python">{`async def file_exists(path: str | Path) -> bool: ...`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Example</h4>
        <CodeBlock language="python">{`from aquilia.filesystem import file_exists

if await file_exists("config.json"):
    config = await read_file("config.json")
else:
    config = DEFAULT_CONFIG`}</CodeBlock>
      </section>

      {/* file_stat */}
      <section id="file_stat" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          file_stat
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Returns file metadata.
        </p>

        <CodeBlock language="python">{`async def file_stat(path: str | Path) -> FileStat: ...

# FileStat fields:
class FileStat:
    size: int           # Size in bytes
    mtime: float        # Modification time (Unix timestamp)
    ctime: float        # Creation time (Unix timestamp)
    atime: float        # Access time (Unix timestamp)
    mode: int           # File mode (permissions)
    is_file: bool       # True if regular file
    is_dir: bool        # True if directory
    is_symlink: bool    # True if symbolic link`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Example</h4>
        <CodeBlock language="python">{`from aquilia.filesystem import file_stat
from datetime import datetime

stat = await file_stat("document.pdf")
print(f"Size: {stat.size} bytes")
print(f"Modified: {datetime.fromtimestamp(stat.mtime)}")
print(f"Is file: {stat.is_file}")`}</CodeBlock>
      </section>

      {/* AsyncFile */}
      <section id="asyncfile" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          AsyncFile
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Async file handle returned by <code className="text-aquilia-500">async_open()</code>. 
          All methods execute in a thread pool.
        </p>

        <CodeBlock language="python">{`class AsyncFile:
    # Reading
    async def read(size: int = -1) -> str | bytes: ...
    async def readline() -> str | bytes: ...
    async def readlines() -> list[str | bytes]: ...
    
    # Writing
    async def write(data: str | bytes) -> int: ...
    async def writelines(lines: Iterable[str | bytes]) -> None: ...
    
    # Positioning
    async def seek(offset: int, whence: int = 0) -> int: ...
    async def tell() -> int: ...
    
    # Sync
    async def flush() -> None: ...
    
    # Properties
    @property
    def name(self) -> str: ...
    @property
    def mode(self) -> str: ...
    @property
    def closed(self) -> bool: ...
    
    # Iteration
    async def __aiter__(self) -> AsyncIterator[str | bytes]: ...`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Example</h4>
        <CodeBlock language="python">{`from aquilia.filesystem import async_open

async with await async_open("data.bin", "rb") as f:
    # Read header
    header = await f.read(4)
    
    # Seek to position
    await f.seek(100)
    
    # Read chunk
    chunk = await f.read(1024)
    
    # Get current position
    pos = await f.tell()`}</CodeBlock>
      </section>

      {/* FileSystem */}
      <section id="filesystem" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          FileSystem
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          DI-injectable service class wrapping all filesystem operations. 
          Provides a consistent interface for dependency injection.
        </p>

        <CodeBlock language="python">{`class FileSystem:
    def __init__(
        config: FileSystemConfig | None = None,  # Optional configuration
    ) -> None: ...
    
    # All standalone functions are available as methods:
    async def read_file(self, path, mode="t", encoding="utf-8") -> str | bytes: ...
    async def write_file(self, path, data, **kwargs) -> None: ...
    async def append_file(self, path, data, **kwargs) -> None: ...
    async def copy_file(self, src, dst, **kwargs) -> None: ...
    async def move_file(self, src, dst, **kwargs) -> None: ...
    async def delete_file(self, path, **kwargs) -> None: ...
    async def file_exists(self, path) -> bool: ...
    async def file_stat(self, path) -> FileStat: ...
    async def list_dir(self, path) -> list[str]: ...
    async def make_dir(self, path, **kwargs) -> None: ...
    async def remove_dir(self, path, **kwargs) -> None: ...
    async def remove_tree(self, path) -> None: ...
    async def copy_tree(self, src, dst, **kwargs) -> None: ...
    
    # Open file
    async def open(self, path, mode="r", **kwargs) -> AsyncFile: ...`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Example</h4>
        <CodeBlock language="python">{`from aquilia.filesystem import FileSystem

# In a controller with DI
class FilesController(Controller):
    prefix = "/files"
    
    def __init__(self, fs: FileSystem):
        self.fs = fs
    
    @GET("/{path:path}")
    async def read(self, ctx: RequestCtx, path: str):
        content = await self.fs.read_file(path)
        return Response.text(content)`}</CodeBlock>
      </section>

      {/* AsyncPath */}
      <section id="asyncpath" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          AsyncPath
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Pathlib-style async path operations. Provides a familiar interface for those 
          who prefer pathlib over standalone functions.
        </p>

        <CodeBlock language="python">{`class AsyncPath:
    def __init__(self, *paths: str | Path) -> None: ...
    
    # Properties (sync)
    @property
    def name(self) -> str: ...
    @property
    def stem(self) -> str: ...
    @property
    def suffix(self) -> str: ...
    @property
    def parent(self) -> AsyncPath: ...
    @property
    def parts(self) -> tuple[str, ...]: ...
    
    # Path operations (sync)
    def __truediv__(self, other: str) -> AsyncPath: ...  # p / "subdir"
    def with_name(self, name: str) -> AsyncPath: ...
    def with_suffix(self, suffix: str) -> AsyncPath: ...
    
    # Async operations
    async def exists(self) -> bool: ...
    async def is_file(self) -> bool: ...
    async def is_dir(self) -> bool: ...
    async def stat(self) -> FileStat: ...
    async def read_text(self, encoding="utf-8") -> str: ...
    async def read_bytes(self) -> bytes: ...
    async def write_text(self, data: str, **kwargs) -> None: ...
    async def write_bytes(self, data: bytes, **kwargs) -> None: ...
    async def mkdir(self, parents=False, exist_ok=False) -> None: ...
    async def rmdir(self) -> None: ...
    async def unlink(self, missing_ok=False) -> None: ...
    async def rename(self, target) -> AsyncPath: ...
    async def iterdir(self) -> AsyncIterator[AsyncPath]: ...
    async def glob(self, pattern) -> AsyncIterator[AsyncPath]: ...`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Example</h4>
        <CodeBlock language="python">{`from aquilia.filesystem import AsyncPath

# Create path
path = AsyncPath("data") / "reports" / "2024"

# Read file
if await path.exists():
    content = await (path / "summary.txt").read_text()

# Iterate directory
async for file in path.iterdir():
    if file.suffix == ".json":
        data = await file.read_text()

# Glob pattern
async for py_file in AsyncPath(".").glob("**/*.py"):
    print(py_file.name)`}</CodeBlock>
      </section>

      {/* Security Functions */}
      <section id="security" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Security Functions
        </h2>

        <h3 className={`text-xl font-semibold mt-8 mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          validate_path
        </h3>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Validates a path for security issues.
        </p>

        <CodeBlock language="python">{`def validate_path(
    path: str | Path,             # Path to validate
    max_length: int = 4096,       # Maximum path length
    allow_absolute: bool = True,  # Allow absolute paths
) -> Path: ...`}</CodeBlock>

        <h3 className={`text-xl font-semibold mt-8 mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          sanitize_filename
        </h3>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Sanitizes a user-provided filename to remove dangerous characters.
        </p>

        <CodeBlock language="python">{`def sanitize_filename(
    filename: str,                # Filename to sanitize
    replacement: str = "_",       # Character to replace dangerous chars with
    max_length: int = 255,        # Maximum filename length
) -> str: ...`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Example</h4>
        <CodeBlock language="python">{`from aquilia.filesystem import validate_path, sanitize_filename

# Validate user input
def handle_upload(user_path: str):
    try:
        safe_path = validate_path(user_path, allow_absolute=False)
    except PathTraversalFault:
        raise HTTPException(400, "Invalid path")
    
    return safe_path

# Sanitize filename
user_filename = "../../etc/passwd"
safe_name = sanitize_filename(user_filename)  # "__etc_passwd"`}</CodeBlock>
      </section>

      {/* Errors */}
      <section id="errors" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <AlertTriangle className="inline w-6 h-6 mr-2 text-amber-500" />
          Errors
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          All filesystem operations raise structured <code className="text-aquilia-500">Fault</code> exceptions 
          with consistent error codes and messages.
        </p>

        <div className={`overflow-x-auto rounded-xl border ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={isDark ? 'bg-white/5' : 'bg-gray-50'}>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Exception</th>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Code</th>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/10' : 'divide-gray-200'}`}>
              {errors.map((e, i) => (
                <tr key={i}>
                  <td className={`px-4 py-3 ${isDark ? 'text-white' : 'text-gray-900'}`}><code>{e.name}</code></td>
                  <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}><code className="text-aquilia-500">{e.code}</code></td>
                  <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{e.desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Error Handling Example</h4>
        <CodeBlock language="python">{`from aquilia.filesystem import (
    read_file,
    FileNotFoundFault,
    PermissionDeniedFault,
    PathTraversalFault,
    FileSystemFault,
)

async def safe_read(path: str) -> str | None:
    try:
        return await read_file(path)
    except PathTraversalFault:
        # Security issue - log and reject
        logger.warning(f"Path traversal attempt: {path}")
        raise HTTPException(400, "Invalid path")
    except FileNotFoundFault:
        return None
    except PermissionDeniedFault:
        raise HTTPException(403, "Access denied")
    except FileSystemFault as e:
        # Catch-all for other filesystem errors
        logger.error(f"Filesystem error: {e}")
        raise HTTPException(500, "Internal error")`}</CodeBlock>
      </section>
    </div>
  )
}
