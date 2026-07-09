import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { NextSteps } from '../../../components/NextSteps'
import { Code, Layers, Terminal } from 'lucide-react'

export function FilesystemController() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      {/* Title Header */}
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Code className="w-4 h-4 animate-pulse" />
          Filesystem / Controller Guide
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          Controller Integration
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          Learn how to inject the FileSystem service, parse and validate file uploads, stream chunked files, check folder directories safely, and handle filesystem faults.
        </p>
      </div>

      {/* Dependency Injection */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-500" />
          Injecting the FileSystem Service
        </h2>
        <p className={`mb-6 ${subtleText}`}>
          The <DocTerm id="filesystem.FileSystem">FileSystem</DocTerm> service handles thread pool offloading and is automatically registered in the DI container.
        </p>

        <p className={`mb-4 ${subtleText}`}>
          Simply declare <DocTerm id="filesystem.FileSystem">FileSystem</DocTerm> as a parameter type in your Controller constructor. Aquilia resolves it automatically using type annotations, without requiring explicit <code className="text-aquilia-500">Inject()</code> defaults:
        </p>
        <CodeBlock language="python" highlightLines={[9, 20]}>{`# modules/files/controllers.py
from aquilia import Controller, GET, POST, RequestCtx, Response
from aquilia.filesystem import FileSystem, FileNotFoundFault, PathTraversalFault

class MediaController(Controller):
    prefix = "/media"

    # Auto-wired via DI using type annotations
    def __init__(self, fs: FileSystem):
        self.fs = fs
        self.storage_root = "./var/media"

    @GET("/read/{filename:path}")
    async def view_file(self, ctx: RequestCtx, filename: str) -> Response:
        # Resolve path safely inside our storage root boundary
        target_path = f"{self.storage_root}/{filename}"
        
        try:
            # FileSystem automatically validates target_path sandboxing
            content = await self.fs.read_file(target_path, sandbox=self.storage_root)
            return Response.text(content)
        except FileNotFoundFault:
            return Response.json({"error": "File does not exist"}, status=404)
        except PathTraversalFault:
            return Response.json({"error": "Illegal path access blocked"}, status=400)`}</CodeBlock>
      </section>

      {/* File Uploads */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4`}>
          Handling File Uploads
        </h2>
        <p className={`mb-6 ${subtleText}`}>
          Process uploaded files safely by running name sanitization and writing bytes asynchronously:
        </p>
        <CodeBlock language="python" highlightLines={[5, 10, 14, 17]}>{`from aquilia.filesystem import sanitize_filename

@POST("/upload")
async def upload(self, ctx: RequestCtx) -> Response:
    file = await ctx.request.file("file")
    if not file:
        return Response.json({"error": "Missing file"}, status=400)
        
    # Sanitize name to avoid malicious shell/path segments
    safe_name = sanitize_filename(file.filename)
    dest_path = f"{self.storage_root}/{safe_name}"
    
    # Read uploaded stream
    content = await file.read()
    
    # Write atomically (dest_path parent is created if missing)
    await self.fs.write_file(dest_path, content, atomic=True, mkdir=True)
    
    return Response.json({"filename": safe_name, "bytes": len(content)}, status=201)`}</CodeBlock>
      </section>

      {/* Directory Browser */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4`}>
          Directory Listing Browser
        </h2>
        <p className={`mb-6 ${subtleText}`}>
          Build a safe file list directory endpoint using <code className="text-aquilia-500">scan_dir</code> and <code className="text-aquilia-500">validate_relative_path</code>:
        </p>
        <CodeBlock language="python" highlightLines={[8, 16, 21]}>{`from aquilia.filesystem import validate_relative_path, file_stat

@GET("/list/{folder:path}")
async def list_folder(self, ctx: RequestCtx, folder: str = "") -> Response:
    # Ensure relative path has no '..' segments
    if folder:
        try:
            folder = validate_relative_path(folder)
        except Exception:
            return Response.json({"error": "Malformed path"}, status=400)
            
    full_path = f"{self.storage_root}/{folder}" if folder else self.storage_root
    
    try:
        # scan_dir returns a list of DirEntry dataclasses
        entries = await self.fs.scan_dir(full_path, sandbox=self.storage_root)
        
        results = []
        for entry in entries:
            # DirEntry holds cached boolean flags
            entry_type = "directory" if entry.is_dir_cached else "file"
            results.append({
                "name": entry.name,
                "type": entry_type,
                "path": entry.path
            })
            
        return Response.json({"folder": folder, "entries": results})
    except FileNotFoundFault:
        return Response.json({"error": "Directory does not exist"}, status=404)`}</CodeBlock>
      </section>

      {/* Fault Management */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Terminal className="w-5 h-5 text-aquilia-500" />
          Handling Filesystem Faults
        </h2>
        <p className={`mb-6 ${subtleText}`}>
          Catch concrete filesystem faults from <code className="text-aquilia-500">aquilia.filesystem</code> to return clean status codes:
        </p>
        <CodeBlock language="python">{`from aquilia.filesystem import (
    FileSystemFault,
    FileNotFoundFault,
    PermissionDeniedFault,
    FileExistsFault,
    DiskFullFault
)

@GET("/info")
async def info(self, ctx: RequestCtx) -> Response:
    try:
        stat = await self.fs.file_stat(f"{self.storage_root}/config.json")
        return Response.json({"size": stat.size, "mtime": stat.mtime})
    except FileNotFoundFault:
        return Response.json({"error": "config.json does not exist"}, status=404)
    except PermissionDeniedFault:
        return Response.json({"error": "System read permissions denied"}, status=403)
    except DiskFullFault:
        return Response.json({"error": "Host disk partition is full"}, status=507)
    except FileSystemFault as e:
        return Response.json({"error": f"I/O error: {e.message}"}, status=500)`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
