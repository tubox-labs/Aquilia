import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Workflow } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function EffectsStorageEffect() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <Workflow className="w-4 h-4" />
          <span>EFFECTS / UNIFIED STORAGE</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Storage Effect
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <DocTerm id="effects.StorageEffect">StorageEffect</DocTerm> provides unified file and object storage operations. Managed by the <DocTerm id="effects.StorageProvider">StorageProvider</DocTerm>, it abstracts filesystem locations and cloud storage backends (AWS S3, Google Cloud Storage, Azure Blobs) into a standard API.
        </p>
      </div>

      {/* Philosophy */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Storage Abstraction Layer</h2>
        <div className={`space-y-6 font-light leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          <p>
            Hardcoding file paths or importing third-party cloud SDKs directly into handlers ties your application logic to a specific cloud provider. The <DocTerm id="effects.StorageEffect">StorageEffect</DocTerm> decouples this connection. Handlers operate on simple keys (e.g., <code className="text-white">"invoices/invoice_123.pdf"</code>) inside a scoped bucket namespace, leaving the backend storage configuration to the provider setup.
          </p>
        </div>
      </section>

      {/* StorageHandle API */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">StorageHandle API</h2>
        <p className={`mb-6 font-light ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          The acquired handle is an instance of <DocTerm id="effects.StorageHandle">StorageHandle</DocTerm>. It manages binary data transfer safely across local filesystems and cloud buckets:
        </p>

        <div className="space-y-8 pl-4 border-l border-aquilia-500/20 text-sm text-gray-400">
          <div>
            <CodeBlock language="python" compact showLineNumbers={false}>{`await handle.read(key: str) -> bytes | None`}</CodeBlock>
            <p className="mt-2 font-light">Reads file contents as raw bytes. Returns <code className="text-aquilia-500">None</code> if the file is missing or connection issues arise.</p>
          </div>
          <div>
            <CodeBlock language="python" compact showLineNumbers={false}>{`await handle.write(key: str, data: bytes) -> None`}</CodeBlock>
            <p className="mt-2 font-light">Writes raw bytes to the specified key. Overwrites existing contents if present. Automatically constructs directory trees if needed on a local filesystem.</p>
          </div>
          <div>
            <CodeBlock language="python" compact showLineNumbers={false}>{`await handle.delete(key: str) -> bool`}</CodeBlock>
            <p className="mt-2 font-light">Deletes the file matching the key. Returns <code className="text-aquilia-500">True</code> if deletion was successful, <code className="text-aquilia-500">False</code> otherwise.</p>
          </div>
          <div>
            <CodeBlock language="python" compact showLineNumbers={false}>{`await handle.exists(key: str) -> bool`}</CodeBlock>
            <p className="mt-2 font-light">Queries the backend to check if a file exists under the key. Returns a boolean status.</p>
          </div>
        </div>
      </section>

      {/* Code Example */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Usage: Profile Avatar Secure Uploader</h2>
        <p className={`mb-6 font-light ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          The example below demonstrates receiving a profile avatar, generating a unique filename, writing it to S3 via the <DocTerm id="effects.StorageHandle">StorageHandle</DocTerm>, and saving the record reference to the database:
        </p>

        <CodeBlock language="python" filename="controllers/avatars.py" highlightLines={[8, 13, 24, 28]}>{`import uuid
from aquilia.controller import Controller, POST, RequestCtx
from aquilia.flow import requires
from aquilia.effects import StorageEffect, DBTx

class AvatarUploadController(Controller):
    # Require both storage bucket access and database transaction
    effects = [
        StorageEffect("user-avatars"),
        DBTx["write"]
    ]

    @POST("/profile/avatar")
    async def upload_avatar(self, ctx: RequestCtx) -> dict:
        storage = ctx.get_effect("Storage")  # StorageHandle instance
        db = ctx.get_effect("DBTx")          # DBTxHandle instance
        
        # 1. Fetch file from multipart request body
        uploaded_file = await ctx.request.file("avatar")
        if not uploaded_file:
            return ctx.json({"error": "No avatar file uploaded"}, status=400)
            
        # 2. Validate file extension
        ext = uploaded_file.filename.split(".")[-1].lower()
        if ext not in ("jpg", "jpeg", "png", "webp"):
            return ctx.json({"error": "Unsupported image format"}, status=400)
            
        # 3. Generate a secure, unique filename key
        secure_key = f"profiles/{ctx.user.id}/{uuid.uuid4().hex}.{ext}"
        
        # 4. Write bytes to the cloud storage bucket
        await storage.write(secure_key, uploaded_file.content)
        
        # 5. Update user avatar reference in database
        await db.execute(
            "UPDATE profiles SET avatar_path = ? WHERE user_id = ?",
            (secure_key, ctx.user.id)
        )
        
        return {"status": "avatar_uploaded", "path": secure_key}`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/subsystem/http" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> HTTP Effect
        </Link>
        <Link to="/docs/subsystem/custom" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          Custom Effects <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
