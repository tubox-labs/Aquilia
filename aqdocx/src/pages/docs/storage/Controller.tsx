import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { NextSteps } from '../../../components/NextSteps'
import { Code, Terminal, Layers } from 'lucide-react'

export function StorageController() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      {/* Title Header */}
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Code className="w-4 h-4 animate-pulse" />
          Unified Storage / Controller Guide
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          Controller Integration
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          Learn how to interact with the Storage Registry inside your HTTP Controllers. This guide covers file uploads, streaming downloads, signed URLs, and structured fault handling.
        </p>
      </div>

      {/* Dependency Injection */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-500" />
          Accessing the Registry
        </h2>
        <p className={`mb-6 ${subtleText}`}>
          The <DocTerm id="storage.StorageRegistry">StorageRegistry</DocTerm> singleton is automatically bound to the DI container when the workspace starts. You can inject it into your controllers directly.
        </p>

        <p className={`mb-4 ${subtleText}`}>
          Simply declare <DocTerm id="storage.StorageRegistry">StorageRegistry</DocTerm> as a parameter type in your Controller constructor. Aquilia resolves it automatically using type annotations, without requiring explicit <code className="text-aquilia-500">Inject()</code> defaults:
        </p>
        <CodeBlock language="python" highlightLines={[9, 21]}>{`# modules/api/controllers.py
from aquilia import Controller, GET, POST, RequestCtx, Response
from aquilia.storage import StorageRegistry

class FilesController(Controller):
    prefix = "/files"

    # Auto-wired via DI using type annotations
    def __init__(self, registry: StorageRegistry):
        self.registry = registry

    @POST("/upload")
    async def upload(self, ctx: RequestCtx) -> Response:
        file = await ctx.request.file("file")
        if not file:
            return Response.json({"error": "No file uploaded"}, status=400)
            
        content = await file.read()
        
        # Save using default backend
        saved_name = await self.registry.default.save(file.filename, content)
        
        return Response.json({
            "status": "success",
            "path": saved_name,
        })`}</CodeBlock>
      </section>

      {/* Streaming Files */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Streaming Downloads
        </h2>
        <p className={`mb-6 ${subtleText}`}>
          To deliver large files efficiently without exhausting server RAM, open files as streams and read them in chunks using the <code className="text-aquilia-500">chunks()</code> generator.
        </p>

        <CodeBlock language="python" highlightLines={[12, 13, 14, 16]}>{`@GET("/download/{filename:path}")
async def download(self, ctx: RequestCtx, filename: str) -> Response:
    backend = self.registry.default
    
    if not await backend.exists(filename):
        return Response.json({"error": "File not found"}, status=404)
        
    metadata = await backend.stat(filename)
    
    async def file_sender():
        # open returns a StorageFile supporting async chunk iteration
        async with await backend.open(filename) as f:
            async for chunk in f.chunks(chunk_size=1024 * 64): # 64KB chunks
                yield chunk
                
    return Response.stream(
        file_sender(),
        headers={
            "Content-Type": metadata.content_type,
            "Content-Length": str(metadata.size),
            "Content-Disposition": f'attachment; filename="{filename.split("/")[-1]}"'
        }
    )`}</CodeBlock>
      </section>

      {/* Signed URLs */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Signed / Presigned URLs
        </h2>
        <p className={`mb-6 ${subtleText}`}>
          For cloud storage backends (S3, GCS, Azure), generate temporary signed URLs to allow clients to download files directly from the cloud.
        </p>
        <CodeBlock language="python" highlightLines={[9]}>{`@GET("/signed-url/{filename:path}")
async def get_url(self, ctx: RequestCtx, filename: str) -> Response:
    backend = self.registry["s3"] # Fetch specific S3 backend alias
    
    if not await backend.exists(filename):
        return Response.json({"error": "File not found"}, status=404)
        
    # Generate URL valid for 30 minutes (1800 seconds)
    url = await backend.url(filename, expire=1800)
    
    return Response.json({
        "url": url,
        "expires_in_seconds": 1800,
    })`}</CodeBlock>
      </section>

      {/* Error Handling */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Terminal className="w-5 h-5 text-aquilia-500" />
          Handling Storage Faults
        </h2>
        <p className={`mb-6 ${subtleText}`}>
          Catch specific storage faults from <code className="text-aquilia-500">aquilia.storage</code> to return clean, appropriate HTTP status codes.
        </p>

        <CodeBlock language="python">{`from aquilia.storage import (
    FileNotFoundError,
    PermissionError,
    StorageError
)

@GET("/info/{filename:path}")
async def file_info(self, ctx: RequestCtx, filename: str) -> Response:
    try:
        metadata = await self.registry.default.stat(filename)
        return Response.json(metadata.to_dict())
        
    except FileNotFoundError:
        # Raised by stat() if key does not exist
        return Response.json({"error": "File does not exist"}, status=404)
        
    except PermissionError:
        # Lacking local read rights or cloud IAM permissions
        return Response.json({"error": "Read permission denied"}, status=403)
        
    except StorageError as e:
        # Base class for other storage faults
        return Response.json({"error": f"Storage system failure: {e.message}"}, status=500)`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
