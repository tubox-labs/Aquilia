import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Shield, Key, Lock, FileText, Server, AlertCircle } from 'lucide-react'
import { Link } from 'react-router-dom'

export function SecurityPage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-10">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-aquilia-500/30 to-aquilia-500/10 flex items-center justify-center">
            <Shield className="w-5 h-5 text-aquilia-400" />
          </div>
          <div>
            <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
                Secure Credential Store
                <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
              </span>
            </h1>
            <p className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>Cryptographic protections, storage layout, and audit logging</p>
          </div>
        </div>

        <p className={`text-lg ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Local environment security is a cornerstone of the Aquilia deployment pipeline. 
          To prevent API tokens from being stored in plain text, committed to version control, or leaked in history files, 
          the framework incorporates a multi-layered cryptographic store called <DocTerm id="provider.RenderCredentialStore">RenderCredentialStore</DocTerm>.
        </p>
      </div>

      {/* Security Model (Timeline-like, No Boxes) */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Lock className="w-5 h-5 text-aquilia-400" />
          Cryptographic Protection Model
        </h2>
        <p className={`mb-8 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The credential store implements a defense-in-depth model, securing Render tokens (stored in the <code>credentials.surp</code> binary file) 
          through a series of cryptographic boundaries:
        </p>

        {/* Vertical Timeline, No Boxes */}
        <div className="relative pl-6 border-l-2 border-aquilia-500/20 space-y-8 ml-3">
          {/* Item 1 */}
          <div className="relative">
            <div className="absolute -left-[33px] top-1 w-4 h-4 rounded-full bg-aquilia-500 border-4 border-black dark:border-black flex items-center justify-center shadow-sm shadow-aquilia-500/50" />
            <h3 className={`text-base font-semibold mb-1 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <Key className="w-4.5 h-4.5 text-aquilia-400" />
              1. Machine-Bound Key Derivation
            </h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Keys are never saved on disk. Instead, the encryption key is derived dynamically using <strong>PBKDF2-HMAC-SHA512</strong> 
              configured with <strong>600,000 iterations</strong>. The derivation payload incorporates machine-specific identifiers:
              host hostname, current user name, hardware platform architecture, and python major/minor version. 
              This prevents credentials from being copied and decrypted on another machine.
            </p>
          </div>

          {/* Item 2 */}
          <div className="relative">
            <div className="absolute -left-[33px] top-1 w-4 h-4 rounded-full bg-aquilia-500 border-4 border-black dark:border-black flex items-center justify-center shadow-sm shadow-aquilia-500/50" />
            <h3 className={`text-base font-semibold mb-1 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <Shield className="w-4.5 h-4.5 text-aquilia-400" />
              2. Authenticated Encryption (AES-256-GCM)
            </h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              The token is encrypted with <strong>AES-256-GCM</strong> using a unique 96-bit random nonce generated for each write operation. 
              This provides authenticated confidentiality, ensuring that any external manipulation of the ciphertext results in decryption failure.
            </p>
          </div>

          {/* Item 3 */}
          <div className="relative">
            <div className="absolute -left-[33px] top-1 w-4 h-4 rounded-full bg-aquilia-500 border-4 border-black dark:border-black flex items-center justify-center shadow-sm shadow-aquilia-500/50" />
            <h3 className={`text-base font-semibold mb-1 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <AlertCircle className="w-4.5 h-4.5 text-aquilia-400" />
              3. Tamper-Proof Plaintext Canary
            </h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              An encrypted plaintext canary (<code>"AQUILIA_CANARY_OK"</code>) is embedded in the binary payload. 
              During the loading process, the canary is decrypted first. If key derivation parameters are incorrect (such as moving the file to another PC), 
              the canary check fails immediately, avoiding partial decrypt errors.
            </p>
          </div>

          {/* Item 4 */}
          <div className="relative">
            <div className="absolute -left-[33px] top-1 w-4 h-4 rounded-full bg-aquilia-500 border-4 border-black dark:border-black flex items-center justify-center shadow-sm shadow-aquilia-500/50" />
            <h3 className={`text-base font-semibold mb-1 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <Server className="w-4.5 h-4.5 text-aquilia-400" />
              4. In-Memory Security & Zeroing
            </h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              To prevent security leaks via core dumps or system memory scraping, the credential store uses Python's 
              <code>ctypes</code> module to overwrite mutable buffers with zeros (<code>ctypes.memset</code>) immediately after use, 
              ensuring sensitive data is purged from memory.
            </p>
          </div>
        </div>
      </section>

      {/* Storage Layout */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <FileText className="w-5 h-5 text-aquilia-400" />
          On-Disk Storage Layout
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Credential items are isolated under the local project workspace configuration folder. 
          The directory is located at: <code>&lt;workspace_root&gt;/.aquilia/providers/render/</code>
        </p>

        <CodeBlock
          filename="Storage Layout"
          language="text"
          code={`.aquilia/
└── providers/
    └── render/
        ├── credentials.surp   # Encrypted token & signing signatures (0o600 permissions)
        ├── config.json         # Non-sensitive workspace metadata (owner name, default region)
        └── audit.log           # File log tracking read, write, and verify events`}
        />
      </section>

      {/* Binary Envelope Format */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Server className="w-5 h-5 text-aquilia-400" />
          Binary Envelope Format
        </h2>
        <p className={`mb-6 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The <code>credentials.surp</code> file follows a structured binary layout, verified strictly on read:
        </p>

        <div className="overflow-x-auto">
          <table className={`w-full text-left text-sm ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
            <thead className={`border-b ${isDark ? 'border-white/10 text-white' : 'border-gray-250 text-gray-900'}`}>
              <tr>
                <th className="py-2 pr-4 font-semibold">Byte Offset</th>
                <th className="py-2 px-4 font-semibold">Field Name</th>
                <th className="py-2 px-4 font-semibold">Size</th>
                <th className="py-2 pl-4 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5' : 'divide-gray-150'}`}>
              <tr>
                <td className="py-2.5 pr-4 font-mono">0 - 3</td>
                <td className="py-2.5 px-4 font-mono">Magic Bytes</td>
                <td className="py-2.5 px-4">4 bytes</td>
                <td className="py-2.5 pl-4">Standard header signature <code>"AQCR"</code></td>
              </tr>
              <tr>
                <td className="py-2.5 pr-4 font-mono">4</td>
                <td className="py-2.5 px-4 font-mono">Version</td>
                <td className="py-2.5 px-4">1 byte</td>
                <td className="py-2.5 pl-4">Envelope version (currently <code>2</code>)</td>
              </tr>
              <tr>
                <td className="py-2.5 pr-4 font-mono">5</td>
                <td className="py-2.5 px-4 font-mono">Cipher ID</td>
                <td className="py-2.5 px-4">1 byte</td>
                <td className="py-2.5 pl-4">Cipher suite choice (e.g. <code>1 = AES-GCM</code>)</td>
              </tr>
              <tr>
                <td className="py-2.5 pr-4 font-mono">6 - 13</td>
                <td className="py-2.5 px-4 font-mono">Timestamp</td>
                <td className="py-2.5 px-4">8 bytes</td>
                <td className="py-2.5 pl-4">Double float indicating write time (big-endian)</td>
              </tr>
              <tr>
                <td className="py-2.5 pr-4 font-mono">14 - 17</td>
                <td className="py-2.5 px-4 font-mono">TTL Seconds</td>
                <td className="py-2.5 px-4">4 bytes</td>
                <td className="py-2.5 pl-4">Expiration limit (0 indicates no expiration)</td>
              </tr>
              <tr>
                <td className="py-2.5 pr-4 font-mono">18 - 49</td>
                <td className="py-2.5 px-4 font-mono">Salt</td>
                <td className="py-2.5 px-4">32 bytes</td>
                <td className="py-2.5 pl-4">Cryptographic salt for key derivation</td>
              </tr>
              <tr>
                <td className="py-2.5 pr-4 font-mono">50 - 61</td>
                <td className="py-2.5 px-4 font-mono">Nonce</td>
                <td className="py-2.5 px-4">12 bytes</td>
                <td className="py-2.5 pl-4">Random GCM initialization vector</td>
              </tr>
              <tr>
                <td className="py-2.5 pr-4 font-mono">62 - 65</td>
                <td className="py-2.5 px-4 font-mono">Token Len</td>
                <td className="py-2.5 px-4">4 bytes</td>
                <td className="py-2.5 pl-4">Size (uint32) of the encrypted payload</td>
              </tr>
              <tr>
                <td className="py-2.5 pr-4 font-mono">66 ...</td>
                <td className="py-2.5 px-4 font-mono">Ciphertext</td>
                <td className="py-2.5 px-4">N bytes</td>
                <td className="py-2.5 pl-4">AES-256-GCM encrypted token</td>
              </tr>
              <tr>
                <td className="py-2.5 pr-4 font-mono">... + 16</td>
                <td className="py-2.5 px-4 font-mono">GCM Auth Tag</td>
                <td className="py-2.5 px-4">16 bytes</td>
                <td className="py-2.5 pl-4">GCM integrity authentication tag</td>
              </tr>
              <tr>
                <td className="py-2.5 pr-4 font-mono">... + 64</td>
                <td className="py-2.5 px-4 font-mono">HMAC</td>
                <td className="py-2.5 px-4">64 bytes</td>
                <td className="py-2.5 pl-4">HMAC-SHA512 checksum covering all fields</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Audit Trails */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <FileText className="w-5 h-5 text-aquilia-400" />
          Audit Logging
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Every interaction with the credential store (such as executing <code>aq provider status</code> or deploying via 
          <code>aq deploy render</code>) writes an entry to <code>audit.log</code>. This creates a secure history trail, 
          letting developers audit authentication actions on a local workstation.
        </p>

        <CodeBlock
          filename="audit.log"
          language="yaml"
          code={`- timestamp: "2026-07-12T16:04:12Z"
  event: "save"
  owner: "Production Workspace"
  region: "oregon"
  metadata: { email: "admin@mycorp.com" }
  status: "success"

- timestamp: "2026-07-12T16:15:33Z"
  event: "load"
  caller: "aq deploy render"
  status: "success"`}
        />
      </section>

      {/* Premium Next Steps */}
      <div className={`mt-14 border-t ${isDark ? 'border-white/10' : 'border-gray-250'} pt-8`}>
        <span className="font-mono text-xs font-bold text-aquilia-400 uppercase tracking-widest mb-4 block">Next Chapters</span>
        <div className="flex flex-col space-y-4">
          <Link
            to="/docs/providers/cli"
            className={`group flex items-center justify-between py-3 border-b ${
              isDark ? 'border-white/5 hover:border-aquilia-500/50' : 'border-gray-150 hover:border-aquilia-500/50'
            } transition-all duration-300`}
          >
            <div className="flex items-center gap-3">
              <span className="font-mono text-sm text-gray-500 group-hover:text-aquilia-400 transition-colors">03</span>
              <div>
                <span className={`font-semibold text-sm ${isDark ? 'text-white' : 'text-gray-900'} group-hover:text-aquilia-300 transition-colors`}>
                  CLI Reference Guide
                </span>
                <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'} mt-0.5`}>
                  Complete command flags, environment variable synchronizations, and CLI diagnostics.
                </p>
              </div>
            </div>
            <ArrowRightIcon />
          </Link>

          <Link
            to="/docs/providers/overview"
            className={`group flex items-center justify-between py-3 border-b ${
              isDark ? 'border-white/5 hover:border-aquilia-500/50' : 'border-gray-150 hover:border-aquilia-500/50'
            } transition-all duration-300`}
          >
            <div className="flex items-center gap-3">
              <span className="font-mono text-sm text-gray-500 group-hover:text-aquilia-400 transition-colors">01</span>
              <div>
                <span className={`font-semibold text-sm ${isDark ? 'text-white' : 'text-gray-900'} group-hover:text-aquilia-300 transition-colors`}>
                  Providers Overview
                </span>
                <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'} mt-0.5`}>
                  Deployment strategy, container building pipelines, and configuration approaches.
                </p>
              </div>
            </div>
            <ArrowRightIcon />
          </Link>
        </div>
      </div>
    </div>
  )
}

function ArrowRightIcon() {
  return (
    <svg
      className="w-5 h-5 text-gray-500 group-hover:text-aquilia-400 group-hover:translate-x-1 transition-all duration-300 shrink-0"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      viewBox="0 0 24 24"
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
    </svg>
  )
}
