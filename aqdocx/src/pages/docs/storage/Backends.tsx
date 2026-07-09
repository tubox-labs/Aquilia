import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { NextSteps } from '../../../components/NextSteps'
import { Server } from 'lucide-react'

export function StorageBackends() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      {/* Title Header */}
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Server className="w-4 h-4 animate-pulse" />
          Storage / Backend Setup
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          Backend Setup Guide
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          A complete walkthrough for setting up local, in-memory, AWS S3, Google Cloud, Azure Blob, SFTP, and Composite storage drivers.
        </p>
      </div>

      {/* Local Filesystem */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Local Filesystem Storage
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Stores files directly in a directory on the local machine. It is pre-installed in the core package and requires no external libraries.
        </p>

        <h4 className="font-semibold mb-2">Workspace Configuration</h4>
        <CodeBlock language="python">{`# workspace.py
from aquilia import Workspace
from aquilia.storage import LocalConfig

workspace = (
    Workspace("myapp")
    .storage(
        default="local",
        backends={
            "local": LocalConfig(
                root="./uploads",
                base_url="/static/uploads/",
                permissions=0o644,
                create_dirs=True
            )
        }
    )
)`}</CodeBlock>

        <h4 className="font-semibold mt-6 mb-2">Standalone Programmatic Setup</h4>
        <CodeBlock language="python">{`from aquilia.storage.backends import LocalStorage
from aquilia.storage.configs import LocalConfig

config = LocalConfig(root="./storage", create_dirs=True)
storage = LocalStorage(config)
await storage.initialize()

await storage.save("notes.txt", b"Local storage active")`}</CodeBlock>
      </section>

      {/* Amazon S3 */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Amazon S3 & S3-Compatible Storage
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Connects to AWS S3, MinIO, Cloudflare R2, or DigitalOcean Spaces. Offloads blocking I/O to a background thread pool.
        </p>

        <h4 className="font-semibold mb-2">1. Install Dependencies</h4>
        <CodeBlock language="bash">{`pip install boto3`}</CodeBlock>

        <h4 className="font-semibold mt-6 mb-2">2. Workspace Configuration</h4>
        <CodeBlock language="python">{`# workspace.py
from aquilia import Workspace
from aquilia.storage import S3Config

workspace = (
    Workspace("myapp")
    .storage(
        default="s3",
        backends={
            "s3": S3Config(
                bucket="my-app-assets",
                region="us-east-1",
                prefix="user_uploads/",
                # Uses AWS IAM Instance Profile/credentials file if keys are omitted:
                access_key=None,
                secret_key=None,
            )
        }
    )
)`}</CodeBlock>

        <h4 className="font-semibold mt-6 mb-2">3. Manual Credentials Override</h4>
        <CodeBlock language="python">{`from aquilia.storage.backends import S3Storage
from aquilia.storage.configs import S3Config

storage = S3Storage(S3Config(
    bucket="my-app-assets",
    region="us-east-1",
    access_key="ACCESS_KEY_ID",
    secret_key="SECRET_ACCESS_KEY",
    endpoint_url="https://minio.mycompany.internal", # Override for MinIO
))`}</CodeBlock>
      </section>

      {/* Google Cloud Storage */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Google Cloud Storage (GCS)
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Integrates with Google Cloud Storage buckets.
        </p>

        <h4 className="font-semibold mb-2">1. Install Dependencies</h4>
        <CodeBlock language="bash">{`pip install google-cloud-storage`}</CodeBlock>

        <h4 className="font-semibold mt-6 mb-2">2. Workspace Configuration</h4>
        <CodeBlock language="python">{`# workspace.py
from aquilia import Workspace
from aquilia.storage import GCSConfig

workspace = (
    Workspace("myapp")
    .storage(
        default="gcs",
        backends={
            "gcs": GCSConfig(
                bucket="my-gcp-bucket",
                project="my-gcp-project-id",
                # Uses GOOGLE_APPLICATION_CREDENTIALS environment variable if None:
                credentials_path="/path/to/service-account-key.json",
                prefix="files/",
            )
        }
    )
)`}</CodeBlock>
      </section>

      {/* Azure Blob Storage */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Azure Blob Storage
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Integrates with Azure Blob Storage containers.
        </p>

        <h4 className="font-semibold mb-2">1. Install Dependencies</h4>
        <CodeBlock language="bash">{`pip install azure-storage-blob`}</CodeBlock>

        <h4 className="font-semibold mt-6 mb-2">2. Workspace Configuration</h4>
        <CodeBlock language="python">{`# workspace.py
from aquilia import Workspace
from aquilia.storage import AzureBlobConfig

workspace = (
    Workspace("myapp")
    .storage(
        default="azure",
        backends={
            "azure": AzureBlobConfig(
                container="media-container",
                connection_string="DefaultEndpointsProtocol=https;AccountName=...",
            )
        }
    )
)`}</CodeBlock>
      </section>

      {/* SFTP Storage */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          SFTP / SSH Storage
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Saves and retrieves files over SFTP.
        </p>

        <h4 className="font-semibold mb-2">1. Install Dependencies</h4>
        <CodeBlock language="bash">{`pip install paramiko`}</CodeBlock>

        <h4 className="font-semibold mt-6 mb-2">2. Workspace Configuration</h4>
        <CodeBlock language="python">{`# workspace.py
from aquilia import Workspace
from aquilia.storage import SFTPConfig

workspace = (
    Workspace("myapp")
    .storage(
        default="sftp",
        backends={
            "sftp": SFTPConfig(
                host="sftp.mypartner.com",
                username="partner_upload",
                password="secure_password", # Or key_path="~/.ssh/id_rsa"
                root="/incoming/uploads",
            )
        }
    )
)`}</CodeBlock>
      </section>

      {/* Composite Routing */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Composite Storage Routing
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          A composite backend delegates read/write requests to other registered backends based on glob patterns matched against the file path.
        </p>

        <CodeBlock language="python">{`# workspace.py
from aquilia import Workspace
from aquilia.storage import CompositeConfig, LocalConfig, S3Config

workspace = (
    Workspace("myapp")
    .storage(
        default="composite",
        backends={
            "composite": CompositeConfig(
                # Register the backends inside the composite configuration
                backends={
                    "local_cache": {"backend": "local", "root": "./cache"},
                    "cloud_s3": {"backend": "s3", "bucket": "cdn-assets"},
                },
                # Setup routing rules (glob pattern -> backend alias name)
                rules={
                    "*.jpg": "cloud_s3",
                    "*.png": "cloud_s3",
                    "*.pdf": "cloud_s3",
                    "*": "local_cache",      # Fallback glob rule
                },
                fallback="local_cache",      # Fallback alias if no rules match
            )
        }
    )
)`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
