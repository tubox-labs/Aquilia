import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { FileText, Zap, Shield, Layers, Settings, Box, Lock } from 'lucide-react'

export function FilesystemOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const features = [
    {
      icon: <Box className="w-5 h-5 text-aquilia-400" />,
      title: 'Zero Dependencies',
      desc: 'Uses only stdlib — no aiofiles or external packages required',
    },
    {
      icon: <Zap className="w-5 h-5 text-amber-400" />,
      title: 'True Async',
      desc: 'All operations run in a thread pool — never blocks the event loop',
    },
    {
      icon: <Shield className="w-5 h-5 text-blue-400" />,
      title: 'Security Built-In',
      desc: 'Path traversal protection, null byte rejection, length limits',
    },
    {
      icon: <Lock className="w-5 h-5 text-purple-400" />,
      title: 'Atomic Writes',
      desc: 'Write to temp file + rename prevents partial/corrupt files',
    },
    {
      icon: <Layers className="w-5 h-5 text-rose-400" />,
      title: 'Streaming Support',
      desc: 'Stream large files without loading into memory',
    },
    {
      icon: <Settings className="w-5 h-5 text-cyan-400" />,
      title: 'DI Integration',
      desc: 'FileSystem service injectable into controllers',
    },
  ]

  const apiOverview = [
    { fn: 'async_open(path, mode)', desc: 'Open file, returns AsyncFile context manager' },
    { fn: 'read_file(path)', desc: 'Read entire file as string or bytes' },
    { fn: 'write_file(path, data)', desc: 'Write data to file (atomic by default)' },
    { fn: 'append_file(path, data)', desc: 'Append data to file' },
    { fn: 'copy_file(src, dst)', desc: 'Copy file from src to dst' },
    { fn: 'move_file(src, dst)', desc: 'Move/rename file' },
    { fn: 'delete_file(path)', desc: 'Delete a file' },
    { fn: 'file_exists(path)', desc: 'Check if path exists and is a file' },
    { fn: 'file_stat(path)', desc: 'Get file metadata (size, mtime, etc.)' },
    { fn: 'list_dir(path)', desc: 'List directory contents' },
    { fn: 'make_dir(path)', desc: 'Create directory (with parents)' },
    { fn: 'remove_dir(path)', desc: 'Remove empty directory' },
    { fn: 'remove_tree(path)', desc: 'Remove directory tree recursively' },
  ]

  const comparison = [
    { feature: 'Dependencies', aq: 'None (stdlib only)', aio: 'External package' },
    { feature: 'Atomic Writes', aq: 'Built-in default', aio: 'Manual' },
    { feature: 'Path Security', aq: 'Built-in validation', aio: 'Manual' },
    { feature: 'File Locking', aq: 'AsyncFileLock class', aio: 'Manual' },
    { feature: 'Temp Files', aq: 'async_tempfile()', aio: 'Manual' },
    { feature: 'Tree Operations', aq: 'copy_tree, remove_tree', aio: 'Manual' },
    { feature: 'Streaming Copy', aq: 'stream_copy()', aio: 'Manual' },
    { feature: 'DI Integration', aq: 'FileSystem service', aio: 'Manual' },
    { feature: 'Metrics', aq: 'FileSystemMetrics', aio: 'None' },
  ]

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <FileText className="w-4 h-4" />
          Filesystem
        </div>
        <h1 className={`text-4xl mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono">
            Filesystem Module
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          High-performance native async file I/O. A drop-in replacement for aiofiles that uses 
          thread pool execution with atomic writes, streaming, and built-in security.
        </p>
      </div>

      {/* Quick Example */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Quick Example
        </h2>

        <CodeBlock language="python">{`from aquilia.filesystem import FileSystem, async_open, read_file, write_file

# Simple file operations
content = await read_file("config.json")
await write_file("output.txt", "Hello, World!")

# Async file handle
async with await async_open("data.csv", "r") as f:
    async for line in f:
        process(line)

# Using FileSystem service (DI-injectable)
fs = FileSystem()
files = await fs.list_dir("./logs")
for file in files:
    stats = await fs.stat(file)
    print(f"{file}: {stats.size} bytes")`}</CodeBlock>
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

      {/* API Overview */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          API Overview
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The module provides standalone functions and a <code className="text-aquilia-500">FileSystem</code> service class:
        </p>

        <div className={`overflow-x-auto rounded-xl border ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
          <table className="w-full">
            <thead>
              <tr className={isDark ? 'bg-white/5' : 'bg-gray-50'}>
                <th className={`px-4 py-3 text-left text-sm font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Function</th>
                <th className={`px-4 py-3 text-left text-sm font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/10' : 'divide-gray-200'}`}>
              {apiOverview.map((row, i) => (
                <tr key={i} className={isDark ? 'hover:bg-white/5' : 'hover:bg-gray-50'}>
                  <td className="px-4 py-3"><code className="text-aquilia-500 text-sm">{row.fn}</code></td>
                  <td className={`px-4 py-3 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{row.desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Atomic Writes */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Atomic Writes
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          By default, <code className="text-aquilia-500">write_file()</code> performs atomic writes to prevent data corruption:
        </p>

        <CodeBlock language="python">{`# This is safe even if the process crashes mid-write
await write_file("config.json", new_config)

# How it works internally:
# 1. Write to temp file: config.json.tmp.abc123
# 2. Sync to disk (fsync)
# 3. Atomic rename: config.json.tmp.abc123 → config.json
# Result: Either old or new content, never partial

# Disable atomic writes if needed (not recommended)
await write_file("log.txt", data, atomic=False)`}</CodeBlock>

        <div className={`mt-4 p-4 rounded-xl border ${isDark ? 'bg-blue-500/10 border-blue-500/30' : 'bg-blue-50 border-blue-200'}`}>
          <p className={`text-sm ${isDark ? 'text-blue-300' : 'text-blue-800'}`}>
            <strong>Why this matters:</strong> Without atomic writes, a crash during write can leave a file 
            with partial content (truncated or mixed old/new data). Atomic writes guarantee the file is 
            always in a consistent state.
          </p>
        </div>
      </section>

      {/* Security */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Security Features
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          All path operations are automatically validated for security:
        </p>

        <div className={`p-6 rounded-xl border ${isDark ? 'bg-[#111] border-white/10' : 'bg-white border-gray-200'}`}>
          <ul className={`space-y-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li className="flex items-start gap-2">
              <Shield className="w-4 h-4 text-aquilia-500 mt-1 shrink-0" />
              <span><strong>Path Traversal Protection</strong> — Rejects paths containing <code>..</code> segments</span>
            </li>
            <li className="flex items-start gap-2">
              <Shield className="w-4 h-4 text-aquilia-500 mt-1 shrink-0" />
              <span><strong>Null Byte Rejection</strong> — Rejects paths containing <code>\x00</code> (C string terminator attack)</span>
            </li>
            <li className="flex items-start gap-2">
              <Shield className="w-4 h-4 text-aquilia-500 mt-1 shrink-0" />
              <span><strong>Path Length Limits</strong> — Rejects paths longer than configurable limit (default: 4096)</span>
            </li>
            <li className="flex items-start gap-2">
              <Shield className="w-4 h-4 text-aquilia-500 mt-1 shrink-0" />
              <span><strong>Filename Sanitization</strong> — <code className="text-aquilia-500">sanitize_filename()</code> removes dangerous characters</span>
            </li>
          </ul>
        </div>

        <CodeBlock language="python">{`from aquilia.filesystem import read_file, validate_path, sanitize_filename
from aquilia.filesystem import PathTraversalFault

# These will raise PathTraversalFault:
await read_file("../../../etc/passwd")  # Traversal attack
await read_file("file\\x00name.txt")     # Null byte injection

# Use validate_path for manual checking
try:
    validate_path(user_provided_path)
except PathTraversalFault:
    raise HTTPException(400, "Invalid path")

# Sanitize user-provided filenames
safe_name = sanitize_filename("my../file\\x00.txt")  # "my_file_.txt"`}</CodeBlock>
      </section>

      {/* AsyncFile */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          AsyncFile Handle
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          For more control, use <code className="text-aquilia-500">async_open()</code> to get an async file handle:
        </p>

        <CodeBlock language="python">{`from aquilia.filesystem import async_open

# Read mode
async with await async_open("data.txt", "r") as f:
    content = await f.read()           # Read all
    first_line = await f.readline()    # Read one line
    lines = await f.readlines()        # Read all lines

# Write mode
async with await async_open("output.txt", "w") as f:
    await f.write("Hello, ")
    await f.write("World!\\n")
    await f.writelines(["Line 1\\n", "Line 2\\n"])

# Binary mode
async with await async_open("image.png", "rb") as f:
    data = await f.read()

# Streaming iteration
async with await async_open("large.csv", "r") as f:
    async for line in f:
        process_line(line)`}</CodeBlock>
      </section>

      {/* Why Not aiofiles */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Why Not aiofiles?
        </h2>
        <div className={`overflow-x-auto rounded-xl border ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
          <table className="w-full">
            <thead>
              <tr className={isDark ? 'bg-white/5' : 'bg-gray-50'}>
                <th className={`px-4 py-3 text-left text-sm font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Feature</th>
                <th className={`px-4 py-3 text-left text-sm font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>aquilia.filesystem</th>
                <th className={`px-4 py-3 text-left text-sm font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>aiofiles</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/10' : 'divide-gray-200'}`}>
              {comparison.map((row, i) => (
                <tr key={i} className={isDark ? 'hover:bg-white/5' : 'hover:bg-gray-50'}>
                  <td className={`px-4 py-3 text-sm font-medium ${isDark ? 'text-white' : 'text-gray-900'}`}>{row.feature}</td>
                  <td className={`px-4 py-3 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{row.aq}</td>
                  <td className={`px-4 py-3 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{row.aio}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Installation */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Installation
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The filesystem module is included in the core Aquilia package. No additional dependencies required.
        </p>
        <CodeBlock language="bash">{`pip install aquilia

# That's it! No additional packages needed.`}</CodeBlock>
      </section>

      {/* Next Steps */}
    </div>
  )
}
