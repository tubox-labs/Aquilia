import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Settings, Play, Zap } from 'lucide-react'

export function FilesystemController() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Settings className="w-4 h-4" />
          Filesystem › Controller Guide
        </div>
        <h1 className={`text-4xl mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono">
            Controller Integration
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Using the filesystem module in Aquilia controllers for file uploads, downloads, 
          and file management.
        </p>
      </div>

      {/* DI Setup */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Settings className="inline w-6 h-6 mr-2 text-aquilia-500" />
          Dependency Injection Setup
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Register the <code className="text-aquilia-500">FileSystem</code> service for injection:
        </p>

        <CodeBlock language="python">{`# modules/files/manifest.py
from aquilia import AppManifest
from aquilia.filesystem import FileSystem, FileSystemConfig

manifest = AppManifest(
    name="files",
    providers=[
        # Default configuration
        FileSystem,
        
        # Or with custom config
        (FileSystem, lambda: FileSystem(
            FileSystemConfig(
                max_path_length=4096,
                default_encoding="utf-8",
                atomic_writes=True,
            )
        )),
    ],
    controllers=[
        "modules.files.controllers.FilesController",
    ],
)`}</CodeBlock>
      </section>

      {/* Basic Controller */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Play className="inline w-6 h-6 mr-2 text-aquilia-500" />
          Basic File Controller
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          A simple controller for reading and writing files:
        </p>

        <CodeBlock language="python">{`# modules/files/controllers.py
from aquilia import Controller, GET, POST, DELETE, RequestCtx, Response
from aquilia.filesystem import (
    FileSystem, read_file, write_file, delete_file, file_exists,
    FileNotFoundFault, PermissionDeniedFault, PathTraversalFault
)

class FilesController(Controller):
    prefix = "/api/files"
    tags = ["files"]
    
    def __init__(self, fs: FileSystem):
        self.fs = fs
        self.base_path = "./storage/files"
    
    @GET("/{path:path}")
    async def read_file(self, ctx: RequestCtx, path: str):
        """Read a file by path."""
        full_path = f"{self.base_path}/{path}"
        
        try:
            content = await self.fs.read_file(full_path)
            return Response.text(content)
        except FileNotFoundFault:
            return Response.json(
                {"error": "File not found"},
                status_code=404
            )
        except PathTraversalFault:
            return Response.json(
                {"error": "Invalid path"},
                status_code=400
            )
    
    @POST("/{path:path}")
    async def write_file(self, ctx: RequestCtx, path: str):
        """Write content to a file."""
        full_path = f"{self.base_path}/{path}"
        body = await ctx.request.body()
        
        try:
            await self.fs.write_file(full_path, body.decode())
            return Response.json({"status": "created"}, status_code=201)
        except PermissionDeniedFault:
            return Response.json(
                {"error": "Permission denied"},
                status_code=403
            )
    
    @DELETE("/{path:path}")
    async def delete_file(self, ctx: RequestCtx, path: str):
        """Delete a file."""
        full_path = f"{self.base_path}/{path}"
        
        try:
            await self.fs.delete_file(full_path)
            return Response.json({"status": "deleted"})
        except FileNotFoundFault:
            return Response.json(
                {"error": "File not found"},
                status_code=404
            )`}</CodeBlock>
      </section>

      {/* File Upload */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          File Upload Controller
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Handle file uploads with validation and storage:
        </p>

        <CodeBlock language="python">{`from aquilia import Controller, POST, RequestCtx, Response
from aquilia.filesystem import (
    FileSystem, write_file, make_dir, file_exists,
    sanitize_filename, async_tempfile
)
import hashlib
import uuid

class UploadController(Controller):
    prefix = "/api/upload"
    tags = ["uploads"]
    
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".pdf", ".txt"}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    
    def __init__(self, fs: FileSystem):
        self.fs = fs
        self.upload_dir = "./storage/uploads"
    
    @POST("/")
    async def upload_file(self, ctx: RequestCtx):
        """Upload a file with validation."""
        form = await ctx.request.form()
        file = form.get("file")
        
        if not file:
            return Response.json(
                {"error": "No file provided"},
                status_code=400
            )
        
        # Validate extension
        original_name = sanitize_filename(file.filename)
        ext = "." + original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""
        
        if ext not in self.ALLOWED_EXTENSIONS:
            return Response.json(
                {"error": f"File type not allowed: {ext}"},
                status_code=400
            )
        
        # Read file content
        content = await file.read()
        
        # Validate size
        if len(content) > self.MAX_FILE_SIZE:
            return Response.json(
                {"error": f"File too large (max {self.MAX_FILE_SIZE} bytes)"},
                status_code=400
            )
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = f"{file_id}{ext}"
        filepath = f"{self.upload_dir}/{filename}"
        
        # Ensure upload directory exists
        await make_dir(self.upload_dir)
        
        # Calculate hash for deduplication
        file_hash = hashlib.sha256(content).hexdigest()
        
        # Save file
        await write_file(filepath, content)
        
        return Response.json({
            "id": file_id,
            "filename": filename,
            "original_name": original_name,
            "size": len(content),
            "hash": file_hash,
        }, status_code=201)
    
    @POST("/chunked")
    async def upload_chunked(self, ctx: RequestCtx):
        """Handle chunked file upload for large files."""
        form = await ctx.request.form()
        
        chunk = form.get("chunk")
        chunk_number = int(form.get("chunk_number", 0))
        total_chunks = int(form.get("total_chunks", 1))
        file_id = form.get("file_id")
        
        if not all([chunk, file_id]):
            return Response.json({"error": "Missing required fields"}, status_code=400)
        
        # Save chunk
        chunk_dir = f"{self.upload_dir}/chunks/{file_id}"
        await make_dir(chunk_dir)
        await write_file(f"{chunk_dir}/{chunk_number}", await chunk.read())
        
        # If all chunks uploaded, combine them
        if chunk_number == total_chunks - 1:
            await self._combine_chunks(file_id, total_chunks)
        
        return Response.json({
            "file_id": file_id,
            "chunk_number": chunk_number,
            "total_chunks": total_chunks,
        })
    
    async def _combine_chunks(self, file_id: str, total_chunks: int):
        """Combine uploaded chunks into final file."""
        from aquilia.filesystem import async_open, remove_tree
        
        chunk_dir = f"{self.upload_dir}/chunks/{file_id}"
        final_path = f"{self.upload_dir}/{file_id}"
        
        async with await async_open(final_path, "wb") as outfile:
            for i in range(total_chunks):
                chunk_path = f"{chunk_dir}/{i}"
                async with await async_open(chunk_path, "rb") as chunk:
                    await outfile.write(await chunk.read())
        
        # Clean up chunks
        await remove_tree(chunk_dir)`}</CodeBlock>
      </section>

      {/* File Download */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          File Download with Streaming
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Stream large files to avoid loading them entirely into memory:
        </p>

        <CodeBlock language="python">{`from aquilia import Controller, GET, RequestCtx, Response
from aquilia.filesystem import (
    FileSystem, stream_read, file_stat, file_exists,
    FileNotFoundFault
)
import mimetypes

class DownloadController(Controller):
    prefix = "/api/download"
    tags = ["downloads"]
    
    def __init__(self, fs: FileSystem):
        self.fs = fs
        self.files_dir = "./storage/files"
    
    @GET("/{file_id}")
    async def download_file(self, ctx: RequestCtx, file_id: str):
        """Download a file with streaming."""
        filepath = f"{self.files_dir}/{file_id}"
        
        if not await file_exists(filepath):
            return Response.json(
                {"error": "File not found"},
                status_code=404
            )
        
        # Get file info
        stat = await file_stat(filepath)
        mime_type, _ = mimetypes.guess_type(file_id) or ("application/octet-stream", None)
        
        # Stream the file
        async def file_stream():
            async for chunk in stream_read(filepath, chunk_size=65536):
                yield chunk
        
        return Response.stream(
            file_stream(),
            media_type=mime_type,
            headers={
                "Content-Length": str(stat.size),
                "Content-Disposition": f'attachment; filename="{file_id}"',
            }
        )
    
    @GET("/{file_id}/range")
    async def download_range(self, ctx: RequestCtx, file_id: str):
        """Support Range requests for video streaming."""
        from aquilia.filesystem import async_open
        
        filepath = f"{self.files_dir}/{file_id}"
        
        if not await file_exists(filepath):
            return Response.json({"error": "File not found"}, status_code=404)
        
        stat = await file_stat(filepath)
        file_size = stat.size
        
        # Parse Range header
        range_header = ctx.request.headers.get("Range")
        if not range_header:
            # No range, return full file
            return await self.download_file(ctx, file_id)
        
        # Parse "bytes=start-end"
        range_match = range_header.replace("bytes=", "").split("-")
        start = int(range_match[0]) if range_match[0] else 0
        end = int(range_match[1]) if range_match[1] else file_size - 1
        
        # Validate range
        if start >= file_size or end >= file_size:
            return Response.text("", status_code=416, headers={
                "Content-Range": f"bytes */{file_size}"
            })
        
        length = end - start + 1
        
        async def range_stream():
            async with await async_open(filepath, "rb") as f:
                await f.seek(start)
                remaining = length
                while remaining > 0:
                    chunk_size = min(65536, remaining)
                    chunk = await f.read(chunk_size)
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk
        
        mime_type, _ = mimetypes.guess_type(file_id) or ("application/octet-stream", None)
        
        return Response.stream(
            range_stream(),
            status_code=206,
            media_type=mime_type,
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(length),
            }
        )`}</CodeBlock>
      </section>

      {/* Directory Listing */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Directory Listing Controller
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Create a file browser API:
        </p>

        <CodeBlock language="python">{`from aquilia import Controller, GET, RequestCtx, Response
from aquilia.filesystem import (
    FileSystem, scan_dir, file_stat, file_exists,
    NotDirectoryFault, validate_path
)
from datetime import datetime

class BrowserController(Controller):
    prefix = "/api/browser"
    tags = ["browser"]
    
    def __init__(self, fs: FileSystem):
        self.fs = fs
        self.root = "./storage/files"
    
    @GET("/")
    @GET("/{path:path}")
    async def list_directory(self, ctx: RequestCtx, path: str = ""):
        """List contents of a directory."""
        # Validate path
        try:
            validate_path(path, allow_absolute=False)
        except Exception:
            return Response.json({"error": "Invalid path"}, status_code=400)
        
        full_path = f"{self.root}/{path}" if path else self.root
        
        if not await file_exists(full_path):
            return Response.json({"error": "Not found"}, status_code=404)
        
        entries = []
        try:
            async for entry in scan_dir(full_path):
                stat = await file_stat(entry.path)
                entries.append({
                    "name": entry.name,
                    "type": "directory" if entry.is_dir else "file",
                    "size": stat.size if entry.is_file else None,
                    "modified": datetime.fromtimestamp(stat.mtime).isoformat(),
                })
        except NotDirectoryFault:
            # It's a file, return file info
            stat = await file_stat(full_path)
            return Response.json({
                "type": "file",
                "name": path.split("/")[-1],
                "size": stat.size,
                "modified": datetime.fromtimestamp(stat.mtime).isoformat(),
            })
        
        # Sort: directories first, then by name
        entries.sort(key=lambda e: (e["type"] != "directory", e["name"].lower()))
        
        return Response.json({
            "path": path,
            "entries": entries,
            "total": len(entries),
        })`}</CodeBlock>
      </section>

      {/* Error Handling */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Comprehensive Error Handling
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Handle all filesystem errors gracefully:
        </p>

        <CodeBlock language="python">{`from aquilia.filesystem import (
    FileSystemFault,
    FileNotFoundFault,
    PermissionDeniedFault,
    FileExistsFault,
    IsDirectoryFault,
    NotDirectoryFault,
    DiskFullFault,
    PathTraversalFault,
    PathTooLongFault,
)
from aquilia.faults import Fault

# Middleware for filesystem error handling
class FileSystemErrorMiddleware:
    async def __call__(self, ctx: RequestCtx, next_handler):
        try:
            return await next_handler(ctx)
        except PathTraversalFault as e:
            # Security issue - don't reveal details
            return Response.json(
                {"error": "Invalid path"},
                status_code=400
            )
        except FileNotFoundFault as e:
            return Response.json(
                {"error": "File not found", "path": e.path},
                status_code=404
            )
        except PermissionDeniedFault as e:
            return Response.json(
                {"error": "Permission denied"},
                status_code=403
            )
        except FileExistsFault as e:
            return Response.json(
                {"error": "File already exists", "path": e.path},
                status_code=409
            )
        except IsDirectoryFault:
            return Response.json(
                {"error": "Path is a directory"},
                status_code=400
            )
        except NotDirectoryFault:
            return Response.json(
                {"error": "Path is not a directory"},
                status_code=400
            )
        except DiskFullFault:
            return Response.json(
                {"error": "Storage full"},
                status_code=507
            )
        except PathTooLongFault:
            return Response.json(
                {"error": "Path too long"},
                status_code=400
            )
        except FileSystemFault as e:
            # Generic filesystem error
            return Response.json(
                {"error": "Filesystem error", "code": e.code},
                status_code=500
            )`}</CodeBlock>
      </section>

      {/* Testing */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Zap className="inline w-6 h-6 mr-2 text-aquilia-500" />
          Testing
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Test filesystem operations using temporary directories:
        </p>

        <CodeBlock language="python">{`import pytest
from aquilia.testing import TestClient
from aquilia.filesystem import (
    FileSystem, async_tempdir, write_file, read_file
)

@pytest.fixture
async def temp_fs():
    """Provide a FileSystem with temp directory."""
    async with await async_tempdir() as tmpdir:
        fs = FileSystem()
        yield fs, tmpdir

@pytest.fixture
async def client(temp_fs):
    """Test client with temp filesystem."""
    fs, tmpdir = temp_fs
    
    # Create test app with temp storage
    from myapp import create_app
    app = create_app(storage_path=tmpdir)
    
    async with TestClient(app) as client:
        yield client, tmpdir

class TestFilesController:
    async def test_read_file(self, client):
        client, tmpdir = client
        
        # Setup: create test file
        await write_file(f"{tmpdir}/test.txt", "Hello, World!")
        
        # Test read
        response = await client.get("/api/files/test.txt")
        assert response.status_code == 200
        assert response.text == "Hello, World!"
    
    async def test_read_nonexistent(self, client):
        client, _ = client
        
        response = await client.get("/api/files/nonexistent.txt")
        assert response.status_code == 404
    
    async def test_path_traversal_blocked(self, client):
        client, _ = client
        
        response = await client.get("/api/files/../../../etc/passwd")
        assert response.status_code == 400
        assert "Invalid path" in response.json()["error"]
    
    async def test_upload_file(self, client):
        client, tmpdir = client
        
        response = await client.post(
            "/api/upload/",
            files={"file": ("test.txt", b"content", "text/plain")}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["size"] == 7
    
    async def test_upload_large_file_rejected(self, client):
        client, _ = client
        
        # Create 20MB file
        large_content = b"x" * (20 * 1024 * 1024)
        
        response = await client.post(
            "/api/upload/",
            files={"file": ("large.bin", large_content, "application/octet-stream")}
        )
        
        assert response.status_code == 400
        assert "too large" in response.json()["error"]`}</CodeBlock>
      </section>

      {/* Next Steps */}
    </div>
  )
}
