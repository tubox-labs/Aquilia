import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { FolderOpen, FileText, Copy, Layers, Search } from 'lucide-react'

export function FilesystemOperations() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const globPatterns = [
    { pattern: '*', matches: 'Any characters except path separator' },
    { pattern: '**', matches: 'Any characters including path separator (recursive)' },
    { pattern: '?', matches: 'Any single character' },
    { pattern: '[abc]', matches: 'Any character in brackets' },
    { pattern: '[!abc]', matches: 'Any character NOT in brackets' },
    { pattern: '{a,b}', matches: 'Either a or b' },
  ]

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <FolderOpen className="w-4 h-4" />
          Filesystem › Operations
        </div>
        <h1 className={`text-4xl mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono">
            File & Directory Operations
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Comprehensive guide to all file and directory operations available in the filesystem module.
        </p>
      </div>

      {/* Directory Operations */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <FolderOpen className="inline w-6 h-6 mr-2 text-aquilia-500" />
          Directory Operations
        </h2>

        {/* list_dir */}
        <div className="mb-10">
          <h3 className={`text-xl font-semibold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            list_dir
          </h3>
          <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Lists contents of a directory. Returns a list of filenames (not full paths).
          </p>

          <CodeBlock language="python">{`async def list_dir(
    path: str | Path,             # Directory path
    pattern: str | None = None,   # Optional glob pattern filter
) -> list[str]: ...`}</CodeBlock>

          <CodeBlock language="python">{`from aquilia.filesystem import list_dir

# List all files
files = await list_dir("./data")
# ['file1.txt', 'file2.json', 'subdir']

# Filter by pattern
json_files = await list_dir("./data", pattern="*.json")
# ['file2.json']`}</CodeBlock>
        </div>

        {/* scan_dir */}
        <div className="mb-10">
          <h3 className={`text-xl font-semibold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            scan_dir
          </h3>
          <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Scans a directory and returns detailed entries with file type information.
          </p>

          <CodeBlock language="python">{`async def scan_dir(
    path: str | Path,             # Directory path
) -> AsyncIterator[DirEntry]: ...

# DirEntry fields:
class DirEntry:
    name: str           # Filename
    path: str           # Full path
    is_file: bool       # True if regular file
    is_dir: bool        # True if directory
    is_symlink: bool    # True if symbolic link`}</CodeBlock>

          <CodeBlock language="python">{`from aquilia.filesystem import scan_dir

# Iterate with type info
async for entry in scan_dir("./data"):
    if entry.is_file:
        print(f"File: {entry.name}")
    elif entry.is_dir:
        print(f"Dir:  {entry.name}")`}</CodeBlock>
        </div>

        {/* make_dir */}
        <div className="mb-10">
          <h3 className={`text-xl font-semibold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            make_dir
          </h3>
          <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Creates a directory. Optionally creates parent directories.
          </p>

          <CodeBlock language="python">{`async def make_dir(
    path: str | Path,             # Directory path
    parents: bool = True,         # Create parent directories
    exist_ok: bool = True,        # Don't error if exists
    mode: int = 0o755,            # Permission mode
) -> None: ...`}</CodeBlock>

          <CodeBlock language="python">{`from aquilia.filesystem import make_dir

# Create directory (with parents by default)
await make_dir("./data/reports/2024/q1")

# Create with specific permissions
await make_dir("./private", mode=0o700)

# Error if exists
await make_dir("./temp", exist_ok=False)  # Raises FileExistsFault if exists`}</CodeBlock>
        </div>

        {/* remove_dir */}
        <div className="mb-10">
          <h3 className={`text-xl font-semibold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            remove_dir
          </h3>
          <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Removes an empty directory.
          </p>

          <CodeBlock language="python">{`async def remove_dir(
    path: str | Path,             # Directory path
    missing_ok: bool = False,     # Don't error if doesn't exist
) -> None: ...`}</CodeBlock>

          <CodeBlock language="python">{`from aquilia.filesystem import remove_dir

# Remove empty directory
await remove_dir("./temp")

# Don't error if missing
await remove_dir("./maybe_exists", missing_ok=True)

# This fails if directory is not empty!
# Use remove_tree() for non-empty directories`}</CodeBlock>
        </div>

        {/* remove_tree */}
        <div className="mb-10">
          <h3 className={`text-xl font-semibold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            remove_tree
          </h3>
          <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Recursively removes a directory and all its contents. Use with caution!
          </p>

          <CodeBlock language="python">{`async def remove_tree(
    path: str | Path,             # Directory path
    missing_ok: bool = False,     # Don't error if doesn't exist
) -> None: ...`}</CodeBlock>

          <CodeBlock language="python">{`from aquilia.filesystem import remove_tree

# Remove directory tree
await remove_tree("./temp_data")

# Safe removal
await remove_tree("./cache", missing_ok=True)`}</CodeBlock>

          <div className={`mt-4 p-4 rounded-xl border ${isDark ? 'bg-amber-500/10 border-amber-500/30' : 'bg-amber-50 border-amber-200'}`}>
            <p className={`text-sm ${isDark ? 'text-amber-300' : 'text-amber-800'}`}>
              <strong>⚠️ Warning:</strong> <code>remove_tree()</code> is destructive and cannot be undone. 
              Always validate the path before calling this function, especially with user-provided input.
            </p>
          </div>
        </div>

        {/* copy_tree */}
        <div className="mb-10">
          <h3 className={`text-xl font-semibold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            copy_tree
          </h3>
          <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Recursively copies a directory tree.
          </p>

          <CodeBlock language="python">{`async def copy_tree(
    src: str | Path,              # Source directory
    dst: str | Path,              # Destination directory
    dirs_exist_ok: bool = False,  # Allow destination to exist
    ignore: Callable | None = None,  # Function to filter files
) -> None: ...`}</CodeBlock>

          <CodeBlock language="python">{`from aquilia.filesystem import copy_tree

# Copy entire directory
await copy_tree("./project", "./project_backup")

# Copy with existing destination
await copy_tree("./src", "./dist", dirs_exist_ok=True)

# Copy with filter
def ignore_pyc(names):
    return [n for n in names if n.endswith('.pyc')]

await copy_tree("./src", "./dist", ignore=ignore_pyc)`}</CodeBlock>
        </div>

        {/* walk */}
        <div className="mb-10">
          <h3 className={`text-xl font-semibold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            walk
          </h3>
          <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Recursively walks a directory tree. Async version of <code className="text-aquilia-500">os.walk()</code>.
          </p>

          <CodeBlock language="python">{`async def walk(
    path: str | Path,             # Root directory
    topdown: bool = True,         # Yield parent before children
    follow_symlinks: bool = False,  # Follow symbolic links
) -> AsyncIterator[tuple[str, list[str], list[str]]]: ...
# Yields: (dirpath, dirnames, filenames)`}</CodeBlock>

          <CodeBlock language="python">{`from aquilia.filesystem import walk

# Find all Python files
async for dirpath, dirnames, filenames in walk("./src"):
    for filename in filenames:
        if filename.endswith(".py"):
            full_path = f"{dirpath}/{filename}"
            print(full_path)

# Skip certain directories
async for dirpath, dirnames, filenames in walk("./project"):
    # Modify dirnames in-place to skip directories
    dirnames[:] = [d for d in dirnames if d not in ('__pycache__', '.git', 'node_modules')]
    
    for filename in filenames:
        print(f"{dirpath}/{filename}")`}</CodeBlock>
        </div>
      </section>

      {/* Temp Files */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <FileText className="inline w-6 h-6 mr-2 text-aquilia-500" />
          Temporary Files
        </h2>

        {/* async_tempfile */}
        <div className="mb-10">
          <h3 className={`text-xl font-semibold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            async_tempfile
          </h3>
          <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Creates a temporary file that is automatically deleted when closed.
          </p>

          <CodeBlock language="python">{`async def async_tempfile(
    mode: str = "w+b",            # File mode
    suffix: str | None = None,    # File suffix
    prefix: str | None = None,    # File prefix
    dir: str | Path | None = None,  # Directory for temp file
    delete: bool = True,          # Delete on close
) -> AsyncTempFile: ...`}</CodeBlock>

          <CodeBlock language="python">{`from aquilia.filesystem import async_tempfile

# Basic usage
async with await async_tempfile() as tmp:
    await tmp.write(b"temporary data")
    await tmp.seek(0)
    data = await tmp.read()
    print(tmp.name)  # /tmp/tmpXXXXXX
# File is automatically deleted

# Text mode with suffix
async with await async_tempfile(mode="w+", suffix=".json") as tmp:
    await tmp.write('{"key": "value"}')
    print(tmp.name)  # /tmp/tmpXXXXXX.json

# Keep the file after closing
async with await async_tempfile(delete=False) as tmp:
    await tmp.write(b"persistent data")
    path = tmp.name
# File still exists at 'path'`}</CodeBlock>
        </div>

        {/* async_tempdir */}
        <div className="mb-10">
          <h3 className={`text-xl font-semibold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            async_tempdir
          </h3>
          <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Creates a temporary directory that is automatically deleted when the context exits.
          </p>

          <CodeBlock language="python">{`async def async_tempdir(
    suffix: str | None = None,    # Directory suffix
    prefix: str | None = None,    # Directory prefix
    dir: str | Path | None = None,  # Parent directory
    delete: bool = True,          # Delete on exit
) -> AsyncTempDir: ...`}</CodeBlock>

          <CodeBlock language="python">{`from aquilia.filesystem import async_tempdir, write_file

# Basic usage
async with await async_tempdir() as tmpdir:
    # Write files in temp directory
    await write_file(f"{tmpdir}/data.txt", "content")
    await write_file(f"{tmpdir}/config.json", '{}')
    
    # Process files...
    print(tmpdir)  # /tmp/tmpXXXXXX
# Directory and contents automatically deleted

# Keep directory
async with await async_tempdir(delete=False, prefix="build_") as tmpdir:
    # Build something...
    print(f"Build output in: {tmpdir}")
# Directory persists at /tmp/build_XXXXXX`}</CodeBlock>
        </div>
      </section>

      {/* File Locking */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="inline w-6 h-6 mr-2 text-aquilia-500" />
          File Locking
        </h2>

        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <code className="text-aquilia-500">AsyncFileLock</code> provides advisory file locking for 
          coordinating access between processes.
        </p>

        <CodeBlock language="python">{`class AsyncFileLock:
    def __init__(
        path: str | Path,             # Lock file path
        timeout: float | None = None,  # Acquisition timeout
        poll_interval: float = 0.1,   # Polling interval
    ) -> None: ...
    
    async def acquire(self) -> None: ...
    async def release(self) -> None: ...
    async def __aenter__(self) -> AsyncFileLock: ...
    async def __aexit__(self, *args) -> None: ...`}</CodeBlock>

        <CodeBlock language="python">{`from aquilia.filesystem import AsyncFileLock, write_file

# Using context manager
async with AsyncFileLock("data.lock"):
    # Exclusive access to shared resource
    data = await read_file("data.json")
    updated = process(data)
    await write_file("data.json", updated)

# With timeout
lock = AsyncFileLock("resource.lock", timeout=5.0)
try:
    async with lock:
        # Critical section
        pass
except TimeoutError:
    print("Could not acquire lock within 5 seconds")

# Manual acquire/release
lock = AsyncFileLock("job.lock")
await lock.acquire()
try:
    # Do work
    pass
finally:
    await lock.release()`}</CodeBlock>

        <div className={`mt-4 p-4 rounded-xl border ${isDark ? 'bg-blue-500/10 border-blue-500/30' : 'bg-blue-50 border-blue-200'}`}>
          <p className={`text-sm ${isDark ? 'text-blue-300' : 'text-blue-800'}`}>
            <strong>Note:</strong> File locks are advisory — they only work if all processes accessing 
            the resource cooperate by using locks. They do not prevent direct file access.
          </p>
        </div>
      </section>

      {/* Streaming Operations */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Copy className="inline w-6 h-6 mr-2 text-aquilia-500" />
          Streaming Operations
        </h2>

        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          For large files, use streaming operations to avoid loading the entire file into memory.
        </p>

        {/* stream_read */}
        <div className="mb-10">
          <h3 className={`text-xl font-semibold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            stream_read
          </h3>
          <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Reads a file in chunks, yielding each chunk as it's read.
          </p>

          <CodeBlock language="python">{`async def stream_read(
    path: str | Path,             # Path to the file
    chunk_size: int = 65536,      # Chunk size in bytes (default: 64KB)
) -> AsyncIterator[bytes]: ...`}</CodeBlock>

          <CodeBlock language="python">{`from aquilia.filesystem import stream_read
import hashlib

# Calculate hash of large file
hasher = hashlib.sha256()
async for chunk in stream_read("large_file.bin"):
    hasher.update(chunk)
file_hash = hasher.hexdigest()

# Stream to HTTP response
@GET("/download/{filename}")
async def download(ctx: RequestCtx, filename: str):
    async def stream():
        async for chunk in stream_read(f"files/{filename}"):
            yield chunk
    return Response.stream(stream(), media_type="application/octet-stream")`}</CodeBlock>
        </div>

        {/* stream_copy */}
        <div className="mb-10">
          <h3 className={`text-xl font-semibold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            stream_copy
          </h3>
          <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Copies a file using streaming to minimize memory usage.
          </p>

          <CodeBlock language="python">{`async def stream_copy(
    src: str | Path,              # Source file path
    dst: str | Path,              # Destination file path
    chunk_size: int = 65536,      # Chunk size in bytes
    progress: Callable | None = None,  # Progress callback
) -> int: ...  # Returns total bytes copied`}</CodeBlock>

          <CodeBlock language="python">{`from aquilia.filesystem import stream_copy

# Basic streaming copy
bytes_copied = await stream_copy("large_video.mp4", "backup.mp4")

# With progress callback
def on_progress(bytes_copied: int, total_bytes: int):
    percent = (bytes_copied / total_bytes) * 100
    print(f"Progress: {percent:.1f}%")

await stream_copy(
    "large_file.zip",
    "copy.zip",
    progress=on_progress
)`}</CodeBlock>
        </div>
      </section>

      {/* Glob Patterns */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Search className="inline w-6 h-6 mr-2 text-aquilia-500" />
          Glob Patterns
        </h2>

        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Use glob patterns to find files matching a pattern.
        </p>

        <CodeBlock language="python">{`async def glob(
    pattern: str,                 # Glob pattern
    root: str | Path = ".",       # Root directory
    recursive: bool = True,       # Allow ** patterns
) -> AsyncIterator[str]: ...`}</CodeBlock>

        <CodeBlock language="python">{`from aquilia.filesystem import glob

# Find all Python files
async for path in glob("**/*.py"):
    print(path)

# Find files in specific directory
async for path in glob("data/*.json"):
    print(path)

# Collect all matches
py_files = [p async for p in glob("**/*.py", root="./src")]`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Glob Pattern Reference</h4>
        <div className={`overflow-x-auto rounded-xl border ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={isDark ? 'bg-white/5' : 'bg-gray-50'}>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Pattern</th>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Matches</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/10' : 'divide-gray-200'}`}>
              {globPatterns.map((p, i) => (
                <tr key={i}>
                  <td className={`px-4 py-3 ${isDark ? 'text-white' : 'text-gray-900'}`}><code>{p.pattern}</code></td>
                  <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{p.matches}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Real-world Examples */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Real-world Examples
        </h2>

        <h3 className={`text-xl font-semibold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Backup Directory with Progress
        </h3>
        <CodeBlock language="python">{`from aquilia.filesystem import (
    copy_tree, async_tempdir, make_dir, 
    remove_tree, walk, file_stat
)
from datetime import datetime

async def backup_directory(source: str, backup_root: str):
    """Creates a timestamped backup of a directory."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{backup_root}/backup_{timestamp}"
    
    # Count files for progress
    total_files = 0
    total_size = 0
    async for dirpath, dirnames, filenames in walk(source):
        for filename in filenames:
            stat = await file_stat(f"{dirpath}/{filename}")
            total_files += 1
            total_size += stat.size
    
    print(f"Backing up {total_files} files ({total_size:,} bytes)")
    
    # Create backup
    await make_dir(backup_path)
    await copy_tree(source, backup_path)
    
    print(f"Backup complete: {backup_path}")
    return backup_path`}</CodeBlock>

        <h3 className={`text-xl font-semibold mt-8 mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Clean Up Old Files
        </h3>
        <CodeBlock language="python">{`from aquilia.filesystem import walk, delete_file, file_stat
from datetime import datetime, timedelta

async def cleanup_old_files(
    directory: str,
    max_age_days: int = 30,
    pattern: str = "*"
):
    """Deletes files older than max_age_days."""
    cutoff = datetime.now().timestamp() - (max_age_days * 86400)
    deleted_count = 0
    deleted_bytes = 0
    
    async for dirpath, dirnames, filenames in walk(directory):
        for filename in filenames:
            filepath = f"{dirpath}/{filename}"
            stat = await file_stat(filepath)
            
            if stat.mtime < cutoff:
                await delete_file(filepath)
                deleted_count += 1
                deleted_bytes += stat.size
    
    print(f"Deleted {deleted_count} files ({deleted_bytes:,} bytes)")
    return deleted_count`}</CodeBlock>

        <h3 className={`text-xl font-semibold mt-8 mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Process Files in Batches
        </h3>
        <CodeBlock language="python">{`from aquilia.filesystem import glob, read_file, write_file
import asyncio

async def process_files_batch(
    pattern: str,
    process_fn,
    batch_size: int = 10
):
    """Processes files matching pattern in batches."""
    files = [f async for f in glob(pattern)]
    
    for i in range(0, len(files), batch_size):
        batch = files[i:i + batch_size]
        
        # Process batch concurrently
        tasks = [process_single(f, process_fn) for f in batch]
        await asyncio.gather(*tasks)
        
        print(f"Processed {min(i + batch_size, len(files))}/{len(files)}")

async def process_single(filepath: str, process_fn):
    content = await read_file(filepath)
    result = await process_fn(content)
    await write_file(filepath, result)`}</CodeBlock>
      </section>
    </div>
  )
}
