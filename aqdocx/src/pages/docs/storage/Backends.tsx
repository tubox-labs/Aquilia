import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Server } from 'lucide-react'

export function StorageBackends() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Server className="w-4 h-4" />
          Storage › Backend Setup
        </div>
        <h1 className={`text-4xl mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono">
            Backend Setup Guide
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Step-by-step setup for each storage backend.
        </p>
      </div>

      {/* Local Storage */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Local Storage
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Store files on the local filesystem. Best for development and single-server deployments.
        </p>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Setup</h4>
        <CodeBlock language="python">{`from aquilia.storage import StorageRegistry, LocalStorage

# In workspace.py
storage_registry = StorageRegistry()
storage_registry.register(
    "local",
    LocalStorage(
        root_path="./storage",      # Relative to workspace root
        create_dirs=True,            # Create directory if missing
        atomic_writes=True,          # Use atomic writes
    )
)
storage_registry.set_default("local")`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Pros & Cons</h4>
        <div className="grid md:grid-cols-2 gap-6">
          <div className={`p-4 rounded-xl border ${isDark ? 'bg-emerald-500/10 border-emerald-500/20' : 'bg-emerald-50 border-emerald-200'}`}>
            <h5 className="font-semibold text-emerald-600 dark:text-emerald-400 mb-2">Pros</h5>
            <ul className={`text-sm space-y-1 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
              <li>• Zero dependencies</li>
              <li>• Fast for small files</li>
              <li>• Simple debugging</li>
              <li>• No external costs</li>
            </ul>
          </div>
          <div className={`p-4 rounded-xl border ${isDark ? 'bg-amber-500/10 border-amber-500/20' : 'bg-amber-50 border-amber-200'}`}>
            <h5 className="font-semibold text-amber-600 dark:text-amber-400 mb-2">Cons</h5>
            <ul className={`text-sm space-y-1 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
              <li>• Not scalable horizontally</li>
              <li>• No CDN integration</li>
              <li>• No built-in redundancy</li>
              <li>• Disk space limits</li>
            </ul>
          </div>
        </div>
      </section>

      {/* S3 Storage */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          AWS S3
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Industry-standard object storage. Recommended for production.
        </p>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>1. Install dependencies</h4>
        <CodeBlock language="bash">{`pip install aioboto3`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>2. Create S3 bucket</h4>
        <CodeBlock language="bash">{`# Using AWS CLI
aws s3 mb s3://my-bucket --region us-east-1

# Set bucket policy (optional)
aws s3api put-bucket-cors --bucket my-bucket --cors-configuration file://cors.json`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>3. Configure credentials</h4>
        <CodeBlock language="bash">{`# Option 1: Environment variables
export AWS_ACCESS_KEY_ID=your-key-id
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_DEFAULT_REGION=us-east-1

# Option 2: AWS CLI configuration
aws configure`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>4. Setup in Aquilia</h4>
        <CodeBlock language="python">{`from aquilia.storage import StorageRegistry, S3Storage

storage_registry = StorageRegistry()
storage_registry.register(
    "s3",
    S3Storage(
        bucket="my-bucket",
        region="us-east-1",
        prefix="uploads/",               # Optional: key prefix
        storage_class="STANDARD",        # Or INTELLIGENT_TIERING
        server_side_encryption="AES256", # Enable encryption
    )
)
storage_registry.set_default("s3")`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>5. Use with CloudFront (CDN)</h4>
        <CodeBlock language="python">{`# Generate signed URLs for direct access
url = await storage.url("video.mp4", expires=3600)
# Returns CloudFront URL if configured`}</CodeBlock>
      </section>

      {/* Google Cloud Storage */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Google Cloud Storage
        </h2>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>1. Install dependencies</h4>
        <CodeBlock language="bash">{`pip install google-cloud-storage aiohttp`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>2. Create bucket</h4>
        <CodeBlock language="bash">{`gsutil mb -p your-project-id -l us-east1 gs://my-bucket`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>3. Setup authentication</h4>
        <CodeBlock language="bash">{`# Download service account key from GCP console
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>4. Configure in Aquilia</h4>
        <CodeBlock language="python">{`from aquilia.storage import StorageRegistry, GCSStorage

storage_registry = StorageRegistry()
storage_registry.register(
    "gcs",
    GCSStorage(
        bucket="my-bucket",
        project="your-project-id",
        credentials="/path/to/service-account.json",
    )
)
storage_registry.set_default("gcs")`}</CodeBlock>
      </section>

      {/* Azure Blob Storage */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Azure Blob Storage
        </h2>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>1. Install dependencies</h4>
        <CodeBlock language="bash">{`pip install azure-storage-blob aiohttp`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>2. Create container</h4>
        <CodeBlock language="bash">{`az storage container create --name my-container --account-name mystorageaccount`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>3. Get connection string</h4>
        <CodeBlock language="bash">{`# From Azure Portal or CLI
az storage account show-connection-string --name mystorageaccount`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>4. Configure in Aquilia</h4>
        <CodeBlock language="python">{`from aquilia.storage import StorageRegistry, AzureBlobStorage

storage_registry = StorageRegistry()
storage_registry.register(
    "azure",
    AzureBlobStorage(
        container="my-container",
        connection_string="DefaultEndpointsProtocol=https;...",
    )
)
storage_registry.set_default("azure")`}</CodeBlock>
      </section>

      {/* SFTP */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          SFTP
        </h2>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>1. Install dependencies</h4>
        <CodeBlock language="bash">{`pip install asyncssh`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>2. Generate SSH key (if needed)</h4>
        <CodeBlock language="bash">{`ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa_sftp
# Add public key to SFTP server's authorized_keys`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>3. Configure in Aquilia</h4>
        <CodeBlock language="python">{`from aquilia.storage import StorageRegistry, SFTPStorage

storage_registry = StorageRegistry()
storage_registry.register(
    "sftp",
    SFTPStorage(
        host="sftp.example.com",
        username="user",
        private_key="~/.ssh/id_rsa_sftp",
        root_path="/uploads",
    )
)
storage_registry.set_default("sftp")`}</CodeBlock>
      </section>

      {/* Composite */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Composite (Multi-Backend)
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Route different file types to different backends.
        </p>

        <CodeBlock language="python">{`from aquilia.storage import (
    StorageRegistry,
    CompositeStorage,
    LocalStorage,
    S3Storage,
)

# Create composite backend
composite = CompositeStorage(
    backends={
        "local": LocalStorage(root_path="./cache"),
        "s3": S3Storage(bucket="my-bucket"),
    },
    rules=[
        # Images and videos to S3
        (r"\\.(jpg|jpeg|png|gif|webp)$", "s3"),
        (r"\\.(mp4|webm|mov)$", "s3"),
        
        # PDFs to S3
        (r"\\.pdf$", "s3"),
        
        # Everything else to local
        (r".*", "local"),
    ],
    default="local",
)

storage_registry = StorageRegistry()
storage_registry.register("composite", composite)
storage_registry.set_default("composite")`}</CodeBlock>
      </section>

      {/* Comparison Table */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Backend Comparison
        </h2>
        <div className={`overflow-x-auto rounded-xl border ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={isDark ? 'bg-white/5' : 'bg-gray-50'}>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Backend</th>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Best For</th>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Cost</th>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Scalability</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/10' : 'divide-gray-200'}`}>
              <tr>
                <td className={`px-4 py-3 font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Local</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Development, single server</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Free</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Low</td>
              </tr>
              <tr>
                <td className={`px-4 py-3 font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Memory</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Testing, caching</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Free</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>N/A</td>
              </tr>
              <tr>
                <td className={`px-4 py-3 font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>S3</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Production, all file types</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>$0.023/GB</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Unlimited</td>
              </tr>
              <tr>
                <td className={`px-4 py-3 font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>GCS</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Production, GCP ecosystem</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>$0.020/GB</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Unlimited</td>
              </tr>
              <tr>
                <td className={`px-4 py-3 font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Azure</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Production, Azure ecosystem</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>$0.018/GB</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Unlimited</td>
              </tr>
              <tr>
                <td className={`px-4 py-3 font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>SFTP</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Legacy systems, compliance</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Varies</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Medium</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
