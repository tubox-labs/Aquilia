import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Settings } from 'lucide-react'

export function StorageConfiguration() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Settings className="w-4 h-4" />
          Storage › Configuration
        </div>
        <h1 className={`text-4xl mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono">
            Backend Configuration
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Configuration options for all storage backends.
        </p>
      </div>

      {/* LocalStorage */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          LocalStorage
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Store files on the local filesystem.
        </p>

        <CodeBlock language="python">{`from aquilia.storage import LocalStorage

storage = LocalStorage(
    root_path="./storage",          # Root directory for files
    create_dirs=True,                # Create directories if missing
    max_path_length=1024,            # Maximum path length
    atomic_writes=True,              # Use atomic writes (temp + rename)
)`}</CodeBlock>
      </section>

      {/* MemoryStorage */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          MemoryStorage
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          In-memory storage for testing.
        </p>

        <CodeBlock language="python">{`from aquilia.storage import MemoryStorage

storage = MemoryStorage(
    max_size=None,                   # Maximum total size in bytes (None = unlimited)
    max_files=None,                  # Maximum number of files (None = unlimited)
)`}</CodeBlock>
      </section>

      {/* S3Storage */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          S3Storage
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          AWS S3 and S3-compatible services.
        </p>

        <CodeBlock language="python">{`from aquilia.storage import S3Storage

storage = S3Storage(
    bucket="my-bucket",              # S3 bucket name (required)
    region="us-east-1",              # AWS region (optional)
    prefix="uploads/",               # Key prefix (optional)
    
    # Authentication (uses AWS credentials chain if omitted)
    access_key_id=None,              # AWS access key ID
    secret_access_key=None,          # AWS secret access key
    
    # Advanced options
    endpoint_url=None,               # Custom endpoint (for S3-compatible services)
    use_ssl=True,                    # Use HTTPS
    verify_ssl=True,                 # Verify SSL certificates
    
    # Upload options
    acl="private",                   # Access control list
    storage_class="STANDARD",        # Storage class
    server_side_encryption=None,     # Encryption method (AES256, aws:kms)
    
    # Performance
    multipart_threshold=8388608,     # Multipart upload threshold (8MB)
    max_concurrency=10,              # Max concurrent uploads/downloads
)`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Environment Variables</h4>
        <CodeBlock language="bash">{`# AWS credentials (if not using access_key_id/secret_access_key)
export AWS_ACCESS_KEY_ID=your-key-id
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_DEFAULT_REGION=us-east-1

# Or use AWS CLI configuration
aws configure`}</CodeBlock>
      </section>

      {/* GCSStorage */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          GCSStorage
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Google Cloud Storage.
        </p>

        <CodeBlock language="python">{`from aquilia.storage import GCSStorage

storage = GCSStorage(
    bucket="my-bucket",              # GCS bucket name (required)
    prefix="uploads/",               # Object prefix (optional)
    
    # Authentication
    credentials=None,                # Credentials object or path to JSON key file
    project=None,                    # GCP project ID
    
    # Advanced options
    predefined_acl=None,             # Predefined ACL (e.g., "publicRead")
    storage_class="STANDARD",        # Storage class
    
    # Performance
    chunk_size=8388608,              # Upload chunk size (8MB)
    timeout=60,                      # Request timeout in seconds
)`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Authentication</h4>
        <CodeBlock language="bash">{`# Set credentials via environment variable
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Or authenticate with gcloud
gcloud auth application-default login`}</CodeBlock>
      </section>

      {/* AzureBlobStorage */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          AzureBlobStorage
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Azure Blob Storage.
        </p>

        <CodeBlock language="python">{`from aquilia.storage import AzureBlobStorage

storage = AzureBlobStorage(
    container="my-container",        # Container name (required)
    account_name=None,               # Storage account name
    account_key=None,                # Storage account key
    connection_string=None,          # Or use connection string
    prefix="uploads/",               # Blob prefix (optional)
    
    # Advanced options
    blob_type="BlockBlob",           # Blob type (BlockBlob, AppendBlob, PageBlob)
    tier=None,                       # Access tier (Hot, Cool, Archive)
    
    # Performance
    max_block_size=4194304,          # Block size (4MB)
    max_single_put_size=67108864,    # Single upload threshold (64MB)
)`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Environment Variables</h4>
        <CodeBlock language="bash">{`# Set connection string
export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;..."`}</CodeBlock>
      </section>

      {/* SFTPStorage */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          SFTPStorage
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          SFTP file transfer.
        </p>

        <CodeBlock language="python">{`from aquilia.storage import SFTPStorage

storage = SFTPStorage(
    host="sftp.example.com",         # SFTP server host (required)
    port=22,                         # SFTP port
    username="user",                 # Username (required)
    password=None,                   # Password (if not using key)
    private_key=None,                # Path to private key file
    private_key_pass=None,           # Private key passphrase
    root_path="/uploads",            # Root directory on server
    
    # Advanced options
    timeout=30,                      # Connection timeout
    allow_agent=True,                # Use SSH agent for authentication
    look_for_keys=True,              # Look for SSH keys in ~/.ssh
    host_key_policy="auto_add",      # Host key policy (auto_add, reject, warn)
)`}</CodeBlock>
      </section>

      {/* CompositeStorage */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          CompositeStorage
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Route files to different backends based on rules.
        </p>

        <CodeBlock language="python">{`from aquilia.storage import CompositeStorage, LocalStorage, S3Storage

composite = CompositeStorage(
    backends={
        "local": LocalStorage(root_path="./storage"),
        "s3": S3Storage(bucket="my-bucket"),
    },
    rules=[
        # Rule format: (pattern, backend_name)
        (r"\\.jpg$", "s3"),           # Images to S3
        (r"\\.png$", "s3"),
        (r"\\.pdf$", "s3"),
        (r".*", "local"),            # Everything else to local
    ],
    default="local",                 # Default backend if no rule matches
)`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Example</h4>
        <CodeBlock language="python">{`# Images go to S3
await composite.save("photo.jpg", image_data)  # → S3

# Documents go to local
await composite.save("document.txt", text_data)  # → Local

# Check which backend was used
backend = composite.get_backend_for_path("photo.jpg")
print(backend)  # "s3"`}</CodeBlock>
      </section>

      {/* Best Practices */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Best Practices
        </h2>

        <div className={`p-6 rounded-xl border ${isDark ? 'bg-[#111] border-white/10' : 'bg-white border-gray-200'}`}>
          <ul className={`space-y-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li><strong>Use environment variables for credentials</strong> — Never hardcode secrets in code</li>
            <li><strong>Enable encryption</strong> — Use server-side encryption for S3, GCS, Azure</li>
            <li><strong>Set appropriate ACLs</strong> — Use private ACLs unless public access is needed</li>
            <li><strong>Configure lifecycle policies</strong> — Automatically transition or delete old files</li>
            <li><strong>Use CompositeStorage</strong> — Route different file types to optimal backends</li>
            <li><strong>Test with MemoryStorage</strong> — Fast, isolated testing without filesystem/network</li>
          </ul>
        </div>
      </section>
    </div>
  )
}
