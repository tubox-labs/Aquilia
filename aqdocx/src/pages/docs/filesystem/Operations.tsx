import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { NextSteps } from '../../../components/NextSteps'
import { FolderOpen, Copy, Layers, Search, Cpu } from 'lucide-react'

export function FilesystemOperations() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      {/* Title Header */}
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <FolderOpen className="w-4 h-4 animate-pulse" />
          Filesystem / Guide
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          File & Directory Operations
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          A comprehensive guide to managing files, directory structures, streaming chunks, path globbing, and atomic operations.
        </p>
      </div>

      {/* Directory Manipulations */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <FolderOpen className="w-5 h-5 text-aquilia-500" />
          Directory Management
        </h2>

        {/* list_dir */}
        <div className="mb-10">
          <h3 className="text-lg font-semibold mb-2">Listing Directory Contents (<code className="text-aquilia-500">list_dir</code>)</h3>
          <p className={`text-sm mb-3 ${subtleText}`}>
            Acquires listing array of filenames (names only, not absolute paths).
          </p>
          <CodeBlock language="python">{`from aquilia.filesystem import list_dir

# Returns list[str] of direct child names (files/folders)
items = await list_dir("./modules")
print(items)  # ['core', 'users', 'auth']`}</CodeBlock>
        </div>

        {/* scan_dir */}
        <div className="mb-10">
          <h3 className="text-lg font-semibold mb-2">Scanning Directory with Metadata (<code className="text-aquilia-500">scan_dir</code>)</h3>
          <p className={`text-sm mb-3 ${subtleText}`}>
            Retrieves list of <DocTerm id="filesystem.DirEntry">DirEntry</DocTerm> objects with cached status details.
          </p>
          <CodeBlock language="python">{`from aquilia.filesystem import scan_dir

entries = await scan_dir("./data")
for entry in entries:
    if entry.is_file_cached:
        print(f"File: {entry.name} at {entry.path}")
    elif entry.is_dir_cached:
        print(f"Directory: {entry.name}")`}</CodeBlock>
        </div>

        {/* make_dir */}
        <div className="mb-10">
          <h3 className="text-lg font-semibold mb-2">Creating Directories (<code className="text-aquilia-500">make_dir</code>)</h3>
          <p className={`text-sm mb-3 ${subtleText}`}>
            Create a folder structure on the host disk safely.
          </p>
          <CodeBlock language="python">{`from aquilia.filesystem import make_dir

# parents=False (raises if parent missing), exist_ok=False (raises if already exists) by default
await make_dir("./uploads/images", parents=True, exist_ok=True)`}</CodeBlock>
        </div>

        {/* remove_dir / remove_tree */}
        <div className="mb-10">
          <h3 className="text-lg font-semibold mb-2">Removing Directories</h3>
          <p className={`text-sm mb-3 ${subtleText}`}>
            Delete empty directories or recursively prune folder trees.
          </p>
          <CodeBlock language="python">{`from aquilia.filesystem import remove_dir, remove_tree

# 1. remove_dir - Deletes empty directory (raises if not empty)
await remove_dir("./temp_folder")

# 2. remove_tree - Deletes directory and all contents recursively
# Silently ignore deletion exceptions if path does not exist
await remove_tree("./cache_files", ignore_errors=True)`}</CodeBlock>
        </div>
      </section>

      {/* Temporary Management */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Cpu className="w-5 h-5 text-aquilia-500" />
          Temporary Files & Directories
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Create self-cleaning files and folders using secure, context-managed wrappers.
        </p>

        <CodeBlock language="python" highlightLines={[4, 6, 8, 12, 14]}>{`from aquilia.filesystem import async_tempfile, async_tempdir

# 1. Temporary File Context
async with async_tempfile(suffix=".csv", prefix="export-") as tmp:
    # tmp is an AsyncFile handle open in w+b mode
    await tmp.write(b"id,name\\n1,Alice")
    await tmp.flush()
    print(f"Temporary file created at: {tmp.name}")
# File is closed and unlinked automatically here

# 2. Temporary Directory Context
async with async_tempdir() as tmpdir:
    # tmpdir is an AsyncPath object
    await (tmpdir / "manifest.json").write_text('{"status": "ok"}')
    print(f"Temporary directory path: {tmpdir.name}")
# Directory and all nested files deleted recursively on block exit`}</CodeBlock>
      </section>

      {/* Advisory Locking */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-500" />
          File Locking
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Utilize cross-process advisory locks to coordinate access to files.
        </p>

        <CodeBlock language="python" highlightLines={[4, 10, 12]}>{`from aquilia.filesystem import AsyncFileLock, read_file, write_file

# Acquire exclusive write lock (blocks until acquired)
async with AsyncFileLock("db.lock"):
    data = await read_file("db.json")
    # Mutate data
    await write_file("db.json", data)

# Acquire lock with a timeout threshold (raises LockAcquisitionError on timeout)
lock = AsyncFileLock("process.lock", timeout=5.0)
try:
    async with lock:
        # Exclusive execution block
        pass
except LockAcquisitionError:
    print("Could not acquire lock, proceeding to fallback")`}</CodeBlock>
      </section>

      {/* Streaming Operations */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Copy className="w-5 h-5 text-aquilia-500" />
          Chunk Streaming
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Stream files in binary chunks to avoid high RAM usage on large files:
        </p>

        <CodeBlock language="python" highlightLines={[4, 8]}>{`from aquilia.filesystem import stream_read, stream_copy

# Stream read a file (yields bytes chunks)
async for chunk in stream_read("archive.tar.gz", chunk_size=1024 * 64):
    process_chunk(chunk)

# Stream copy directly from source to destination
bytes_copied = await stream_copy("large.mp4", "backup.mp4", chunk_size=1024 * 1024)`}</CodeBlock>
      </section>

      {/* Path Globbing */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Search className="w-5 h-5 text-aquilia-500" />
          Path Globbing
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Search directory trees for files matching glob rules using the <DocTerm id="filesystem.AsyncPath">AsyncPath</DocTerm> model:
        </p>
        <CodeBlock language="python" highlightLines={[3, 6]}>{`from aquilia.filesystem import AsyncPath

root = AsyncPath("./src")

# Find all python files recursively
async for filepath in root.glob("**/*.py"):
    print(f"Found code: {filepath.name} (Parent: {filepath.parent.name})")`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
