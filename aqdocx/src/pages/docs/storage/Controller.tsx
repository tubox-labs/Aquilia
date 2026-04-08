import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Code } from 'lucide-react'

export function StorageController() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Code className="w-4 h-4" />
          Storage › Controller Guide
        </div>
        <h1 className={`text-4xl mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono">
            Controller Integration
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Using storage in Aquilia controllers.
        </p>
      </div>

      {/* Dependency Injection */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Dependency Injection
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Inject storage into controllers via the DI container.
        </p>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>1. Register in workspace</h4>
        <CodeBlock language="python">{`# workspace.py
from aquilia import Workspace, Module
from aquilia.storage import StorageRegistry, S3Storage

workspace = Workspace(
    name="myapp",
    modules=[
        Module(name="api", path="modules/api"),
    ],
)

# Setup storage backend
storage = StorageRegistry()
storage.register("s3", S3Storage(bucket="my-bucket"))
storage.set_default("s3")

# Register in DI container
workspace.container.register_singleton(StorageRegistry, lambda: storage)`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>2. Inject in controller</h4>
        <CodeBlock language="python">{`from aquilia import Controller, GET, POST, RequestCtx, Response
from aquilia.storage import StorageRegistry

class UploadsController(Controller):
    prefix = "/uploads"
    
    def __init__(self, storage: StorageRegistry):
        self.storage = storage
    
    @GET("/{filename}")
    async def download(self, ctx: RequestCtx):
        filename = ctx.params["filename"]
        
        # Get file content
        content = await self.storage.open(filename)
        
        return Response.bytes(
            content,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    
    @POST("/")
    async def upload(self, ctx: RequestCtx):
        # Get uploaded file
        file = await ctx.request.file("file")
        if not file:
            return Response.json({"error": "No file provided"}, status=400)
        
        # Save to storage
        content = await file.read()
        await self.storage.save(file.filename, content)
        
        return Response.json({
            "filename": file.filename,
            "size": len(content)
        })`}</CodeBlock>
      </section>

      {/* File Upload */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          File Upload
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Handle multipart file uploads.
        </p>

        <CodeBlock language="python">{`from aquilia import Controller, POST, RequestCtx, Response
from aquilia.storage import StorageRegistry
import uuid
from pathlib import Path

class UploadController(Controller):
    prefix = "/upload"
    
    def __init__(self, storage: StorageRegistry):
        self.storage = storage
    
    @POST("/single")
    async def upload_single(self, ctx: RequestCtx):
        """Upload a single file."""
        file = await ctx.request.file("file")
        if not file:
            return Response.json({"error": "No file"}, status=400)
        
        # Generate unique filename
        ext = Path(file.filename).suffix
        filename = f"{uuid.uuid4()}{ext}"
        
        # Save file
        content = await file.read()
        await self.storage.save(filename, content)
        
        # Get metadata
        metadata = await self.storage.stat(filename)
        
        return Response.json({
            "filename": filename,
            "original_name": file.filename,
            "size": metadata.size,
            "content_type": metadata.content_type,
        })
    
    @POST("/multiple")
    async def upload_multiple(self, ctx: RequestCtx):
        """Upload multiple files."""
        files = await ctx.request.files("files")
        if not files:
            return Response.json({"error": "No files"}, status=400)
        
        results = []
        for file in files:
            ext = Path(file.filename).suffix
            filename = f"{uuid.uuid4()}{ext}"
            
            content = await file.read()
            await self.storage.save(filename, content)
            
            results.append({
                "filename": filename,
                "original_name": file.filename,
                "size": len(content),
            })
        
        return Response.json({
            "count": len(results),
            "files": results
        })`}</CodeBlock>
      </section>

      {/* Streaming Large Files */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Streaming Large Files
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Stream files without loading them entirely into memory.
        </p>

        <CodeBlock language="python">{`from aquilia import Controller, GET, RequestCtx, Response
from aquilia.storage import StorageRegistry

class StreamController(Controller):
    prefix = "/stream"
    
    def __init__(self, storage: StorageRegistry):
        self.storage = storage
    
    @GET("/{filename}")
    async def stream_file(self, ctx: RequestCtx):
        """Stream a large file."""
        filename = ctx.params["filename"]
        
        # Check if file exists
        if not await self.storage.exists(filename):
            return Response.json({"error": "File not found"}, status=404)
        
        # Get metadata for headers
        metadata = await self.storage.stat(filename)
        
        # Stream the file
        async def stream():
            file = await self.storage.open_stream(filename)
            try:
                while True:
                    chunk = await file.read(65536)  # 64KB chunks
                    if not chunk:
                        break
                    yield chunk
            finally:
                await file.close()
        
        return Response.stream(
            stream(),
            headers={
                "Content-Type": metadata.content_type,
                "Content-Length": str(metadata.size),
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )`}</CodeBlock>
      </section>

      {/* Signed URLs */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Signed URLs
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Generate temporary URLs for direct client access (S3/GCS/Azure).
        </p>

        <CodeBlock language="python">{`from aquilia import Controller, GET, POST, RequestCtx, Response
from aquilia.storage import StorageRegistry
import uuid

class MediaController(Controller):
    prefix = "/media"
    
    def __init__(self, storage: StorageRegistry):
        self.storage = storage
    
    @POST("/upload")
    async def upload(self, ctx: RequestCtx):
        """Upload a file and return a signed URL."""
        file = await ctx.request.file("file")
        if not file:
            return Response.json({"error": "No file"}, status=400)
        
        # Save file
        filename = f"media/{uuid.uuid4()}.{file.filename.split('.')[-1]}"
        content = await file.read()
        await self.storage.save(filename, content)
        
        # Generate signed URL (expires in 1 hour)
        url = await self.storage.url(filename, expires=3600)
        
        return Response.json({
            "filename": filename,
            "url": url,
            "expires_in": 3600,
        })
    
    @GET("/{path:path}")
    async def get_url(self, ctx: RequestCtx):
        """Get a signed URL for an existing file."""
        path = ctx.params["path"]
        
        if not await self.storage.exists(path):
            return Response.json({"error": "File not found"}, status=404)
        
        # Get expiry from query params (default 1 hour)
        expires = int(ctx.request.query.get("expires", 3600))
        
        url = await self.storage.url(path, expires=expires)
        
        return Response.json({
            "url": url,
            "expires_in": expires,
        })`}</CodeBlock>
      </section>

      {/* Error Handling */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Error Handling
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Handle storage errors gracefully.
        </p>

        <CodeBlock language="python">{`from aquilia import Controller, GET, RequestCtx, Response
from aquilia.storage import (
    StorageRegistry,
    FileNotFoundError,
    PermissionError,
    PathTraversalError,
    StorageBackendError,
)
import logging

logger = logging.getLogger(__name__)

class SafeStorageController(Controller):
    prefix = "/files"
    
    def __init__(self, storage: StorageRegistry):
        self.storage = storage
    
    @GET("/{filename}")
    async def download(self, ctx: RequestCtx):
        filename = ctx.params["filename"]
        
        try:
            # Attempt to read file
            content = await self.storage.open(filename)
            metadata = await self.storage.stat(filename)
            
            return Response.bytes(
                content,
                headers={
                    "Content-Type": metadata.content_type,
                    "Content-Disposition": f'attachment; filename="{filename}"'
                }
            )
            
        except PathTraversalError:
            logger.warning(f"Path traversal attempt: {filename}")
            return Response.json({"error": "Invalid path"}, status=400)
            
        except FileNotFoundError:
            return Response.json({"error": "File not found"}, status=404)
            
        except PermissionError:
            logger.error(f"Permission denied: {filename}")
            return Response.json({"error": "Access denied"}, status=403)
            
        except StorageBackendError as e:
            logger.error(f"Backend error: {e}")
            return Response.json({"error": "Storage error"}, status=503)
            
        except Exception as e:
            logger.exception("Unexpected error")
            return Response.json({"error": "Internal error"}, status=500)`}</CodeBlock>
      </section>

      {/* Image Upload with Validation */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Image Upload with Validation
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Validate image types, size, and dimensions.
        </p>

        <CodeBlock language="python">{`from aquilia import Controller, POST, RequestCtx, Response
from aquilia.storage import StorageRegistry
from PIL import Image
import io
import uuid

class ImageController(Controller):
    prefix = "/images"
    
    ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
    MAX_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_DIMENSION = 4096
    
    def __init__(self, storage: StorageRegistry):
        self.storage = storage
    
    @POST("/upload")
    async def upload(self, ctx: RequestCtx):
        file = await ctx.request.file("image")
        if not file:
            return Response.json({"error": "No file"}, status=400)
        
        # Read content
        content = await file.read()
        
        # Validate size
        if len(content) > self.MAX_SIZE:
            return Response.json(
                {"error": f"File too large (max {self.MAX_SIZE} bytes)"},
                status=400
            )
        
        # Validate type
        try:
            img = Image.open(io.BytesIO(content))
            mime = f"image/{img.format.lower()}"
            
            if mime not in self.ALLOWED_TYPES:
                return Response.json(
                    {"error": f"Invalid type (allowed: {self.ALLOWED_TYPES})"},
                    status=400
                )
            
            # Validate dimensions
            width, height = img.size
            if width > self.MAX_DIMENSION or height > self.MAX_DIMENSION:
                return Response.json(
                    {"error": f"Image too large (max {self.MAX_DIMENSION}px)"},
                    status=400
                )
        except Exception:
            return Response.json({"error": "Invalid image"}, status=400)
        
        # Save image
        filename = f"images/{uuid.uuid4()}.{img.format.lower()}"
        await self.storage.save(filename, content)
        
        return Response.json({
            "filename": filename,
            "width": width,
            "height": height,
            "format": img.format,
            "size": len(content),
        })`}</CodeBlock>
      </section>

      {/* Next Steps */}
    </div>
  )
}
