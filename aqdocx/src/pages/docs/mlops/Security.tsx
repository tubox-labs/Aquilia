import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Brain } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function MLOpsSecurity() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Brain className="w-4 h-4" />
          MLOps / Security
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Security
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Comprehensive security for ML model artifacts and access control. Includes role-based
          access control (RBAC) with 4 built-in roles and 8 permissions, AES-128-CBC blob encryption,
          and HMAC/RSA artifact signing.
        </p>
      </div>

      {/* RBAC */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Role-Based Access Control</h2>

        <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Permissions</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          {[
            'MODEL_READ',
            'MODEL_WRITE',
            'MODEL_DELETE',
            'MODEL_DEPLOY',
            'REGISTRY_READ',
            'REGISTRY_WRITE',
            'ADMIN_READ',
            'ADMIN_WRITE',
          ].map((perm) => (
            <div key={perm} className={`p-3 rounded-lg text-center ${isDark ? 'bg-white/5' : 'bg-gray-50'}`}>
              <code className="text-aquilia-500 text-xs font-mono">{perm}</code>
            </div>
          ))}
        </div>

        <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Built-in Roles</h3>
        <div className={boxClass}>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className={`text-left ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  <th className="pb-2 pr-4">Role</th>
                  <th className="pb-2">Permissions</th>
                </tr>
              </thead>
              <tbody className={isDark ? 'text-gray-300' : 'text-gray-700'}>
                {[
                  ['VIEWER', 'MODEL_READ, REGISTRY_READ'],
                  ['DEVELOPER', 'MODEL_READ, MODEL_WRITE, REGISTRY_READ, REGISTRY_WRITE'],
                  ['DEPLOYER', 'MODEL_READ, MODEL_WRITE, MODEL_DEPLOY, REGISTRY_READ, REGISTRY_WRITE'],
                  ['ADMIN', 'All 8 permissions'],
                ].map(([role, perms], i) => (
                  <tr key={i} className={`border-t ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
                    <td className="py-2 pr-4 font-mono text-aquilia-500">{role}</td>
                    <td className={`py-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{perms}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <CodeBlock language="python" code={`from aquilia.mlops.security.rbac import RBACManager, Permission

rbac = RBACManager()

# Assign a role to a user
rbac.assign_role("alice", "DEPLOYER")
rbac.assign_role("bob", "VIEWER")

# Check permission
if rbac.check_permission("alice", Permission.MODEL_DEPLOY):
    await deploy_model(...)  # Allowed

if rbac.check_permission("bob", Permission.MODEL_WRITE):
    ...  # This will return False — VIEWER can't write

# Get all permissions for a user
perms = rbac.get_user_permissions("alice")
# {Permission.MODEL_READ, Permission.MODEL_WRITE, Permission.MODEL_DEPLOY,
#  Permission.REGISTRY_READ, Permission.REGISTRY_WRITE}

# Create custom roles
rbac.create_role("ML_ENGINEER", permissions=[
    Permission.MODEL_READ,
    Permission.MODEL_WRITE,
    Permission.MODEL_DEPLOY,
    Permission.REGISTRY_READ,
    Permission.REGISTRY_WRITE,
    Permission.ADMIN_READ,
])

# Role hierarchy enforcement
rbac.assign_role("charlie", "ML_ENGINEER")`} />
      </section>

      {/* Encryption */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Blob Encryption</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Encrypt model artifacts at rest using Fernet (AES-128-CBC with HMAC-SHA256 authentication).
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops.security.encryption import BlobEncryptor, EncryptionManager

# Low-level encryption
encryptor = BlobEncryptor()

# Generate a new encryption key
key = encryptor.generate_key()

# Encrypt model artifact
encrypted_data = encryptor.encrypt(model_bytes, key)

# Decrypt
decrypted_data = encryptor.decrypt(encrypted_data, key)

# High-level EncryptionManager (wraps BlobEncryptor)
manager = EncryptionManager(key=key)

# Encrypt a file
await manager.encrypt_file("./model.pt", "./model.pt.enc")

# Decrypt a file
await manager.decrypt_file("./model.pt.enc", "./model.pt")

# Key properties:
# - Algorithm: Fernet (AES-128-CBC + HMAC-SHA256)
# - Key size: 256 bits (128 bits encryption + 128 bits signing)
# - Authentication: Built into Fernet (prevents tampering)
# - Padding: PKCS7 (automatic)`} />
      </section>

      {/* Artifact Signing */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Artifact Signing</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Cryptographically sign model archives to verify integrity and provenance.
          Two algorithms are supported: HMAC-SHA256 for shared-secret and RSA-PSS for asymmetric signing.
        </p>

        <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>HMAC Signing</h3>
        <CodeBlock language="python" code={`from aquilia.mlops.security.signing import ArtifactSigner

signer = ArtifactSigner(algorithm="hmac", secret_key="my-signing-secret")

# Sign an archive
signature = signer.sign("./sentiment-v2.aquilia")
# Returns hex-encoded HMAC-SHA256 signature

# Verify
is_valid = signer.verify("./sentiment-v2.aquilia", signature)
# Returns True if archive hasn't been tampered with`} />

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>RSA-PSS Signing</h3>
        <CodeBlock language="python" code={`from aquilia.mlops.security.signing import ArtifactSigner

# Generate RSA key pair
signer = ArtifactSigner(
    algorithm="rsa",
    private_key_path="./keys/private.pem",
    public_key_path="./keys/public.pem",
)

# Sign with private key
signature = signer.sign("./sentiment-v2.aquilia")

# Verify with public key (can be distributed)
verifier = ArtifactSigner(
    algorithm="rsa",
    public_key_path="./keys/public.pem",
)
is_valid = verifier.verify("./sentiment-v2.aquilia", signature)

# RSA-PSS properties:
# - Algorithm: RSASSA-PSS with SHA-256
# - Key size: 2048 bits (configurable)
# - Salt length: Max (automatic)
# - Non-repudiation: Only private key holder can sign`} />
      </section>

      {/* Integration with Registry */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Registry Integration</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Security is automatically integrated with the model registry for end-to-end artifact protection.
        </p>
        <CodeBlock language="python" code={`# Full secure workflow:

# 1. Build modelpack
pack = await builder.build(model, manifest)

# 2. Sign the archive
signature = signer.sign(pack.archive_path)
pack.metadata["signature"] = signature

# 3. Encrypt before upload
encrypted = await manager.encrypt_file(pack.archive_path)

# 4. Push to registry (with RBAC check)
if rbac.check_permission(user, Permission.REGISTRY_WRITE):
    await registry.publish(encrypted, metadata=pack.metadata)

# 5. On fetch: decrypt + verify
archive = await registry.fetch("sentiment", "2.1.0")
if not signer.verify(archive, metadata["signature"]):
    raise SecurityFault("Signature verification failed")
decrypted = await manager.decrypt_file(archive)`} />
      </section>

      <NextSteps
        items={[
          { text: 'Explainability', link: '/docs/mlops/explain' },
          { text: 'Deployment', link: '/docs/mlops/deployment' },
          { text: 'Modelpack Builder', link: '/docs/mlops/modelpack' },
          { text: 'MLOps Tutorial', link: '/docs/mlops/tutorial' },
        ]}
      />
    </div>
  )
}
