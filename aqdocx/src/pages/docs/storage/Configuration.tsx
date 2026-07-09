import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { NextSteps } from '../../../components/NextSteps'
import { Settings, ShieldAlert, Info } from 'lucide-react'

export function StorageConfiguration() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      {/* Title Header */}
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Settings className="w-4 h-4 animate-pulse" />
          Unified Storage / Configuration
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          Storage Configuration
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          A complete guide to configuring unified storage backends inside your Aquilia workspace using typed configuration dataclasses.
        </p>
      </div>

      {/* Integration Configuration Styles */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Integration Configuration Styles
        </h2>
        <p className={`mb-6 ${subtleText}`}>
          Aquilia supports two styles of declaring subsystem integrations within <code className="text-aquilia-500">workspace.py</code>: the legacy builder-class style and the modern typed-dataclass style.
        </p>

        {/* Modern Style */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-3">
            <Info className="w-5 h-5 text-emerald-400" />
            <h3 className="text-lg font-semibold">Modern Style: Composed Dataclasses (Recommended)</h3>
          </div>
          <p className={`text-sm mb-4 ${subtleText}`}>
            Construct the <DocTerm id="storage.StorageIntegration">StorageIntegration</DocTerm> class directly. This ensures compile-time validation, IDE type hinting, and strict parameter checking.
          </p>
          <CodeBlock language="python" highlightLines={[9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26]}>{`# workspace.py
from aquilia import Workspace, Module
from aquilia.integrations import StorageIntegration
from aquilia.storage.configs import LocalConfig, S3Config

workspace = (
    Workspace("myapp")
    .module(Module("core"))
    .integrate(StorageIntegration(
        default="local",
        backends={
            "local": LocalConfig(
                root="./uploads",
                base_url="/static/uploads/",
                permissions=0o644,
                dir_permissions=0o755,
                create_dirs=True
            ),
            "s3": S3Config(
                bucket="my-production-bucket",
                region="us-east-1",
                prefix="media/",
                presigned_expiry=3600
            )
        }
    ))
)`}</CodeBlock>
        </div>

        {/* Legacy Style */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-3">
            <ShieldAlert className="w-5 h-5 text-amber-500" />
            <h3 className="text-lg font-semibold text-amber-500">Legacy Style: Static Integration Builders</h3>
          </div>
          <p className={`text-sm mb-4 ${subtleText}`}>
            The legacy <code className="text-aquilia-500">.storage()</code> or <code className="text-aquilia-500">Integration.storage()</code> helper delegates to the modern <code className="text-aquilia-500">StorageIntegration</code> under the hood. Avoid this in new projects.
          </p>
          <CodeBlock language="python" highlightLines={[7, 8, 9, 10, 11, 12]}>{`# workspace.py (Legacy)
from aquilia import Workspace
from aquilia.storage import LocalConfig

workspace = (
    Workspace("myapp")
    .storage(
        default="local",
        backends={
            "local": LocalConfig(root="./storage")
        }
    )
)`}</CodeBlock>
          <div className="group relative overflow-hidden rounded-xl bg-amber-500/5 border border-amber-500/10 p-4 mt-3">
            <p className="text-xs leading-relaxed text-amber-400">
              <strong>Warning:</strong> The legacy static helper <code className="text-aquilia-500">.storage()</code> is deprecated and will be removed in a future release. Migrate to direct constructor calls using <code className="text-aquilia-500">StorageIntegration</code>.
            </p>
          </div>
        </div>
      </section>

      {/* Configuration Dataclasses */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Backend Configuration Options
        </h2>

        {/* LocalConfig */}
        <div className="mb-12">
          <h3 className={`text-xl font-bold mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
            <DocTerm id="storage.LocalConfig">LocalConfig</DocTerm>
          </h3>
          <p className={`text-sm mb-4 ${subtleText}`}>
            Configures the local disk backend. Inherits from <code className="text-aquilia-500">StorageConfig</code>.
          </p>
          <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl mb-4">
            <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
              <thead>
                <tr className="border-b border-white/5 bg-white/5">
                  <th className="text-left py-3 px-6 font-semibold text-aquilia-500 w-44">Attribute</th>
                  <th className="text-left py-3 px-6">Type</th>
                  <th className="text-left py-3 px-6">Default</th>
                  <th className="text-left py-3 px-6">Description</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {[
                  ['root', 'str', '"./storage"', 'Local directory path where files are read/written.'],
                  ['base_url', 'str', '"/storage/"', 'Public HTTP URL prefix for file serving.'],
                  ['permissions', 'int', '0o644', 'Octal permission integer for saved files.'],
                  ['dir_permissions', 'int', '0o755', 'Octal permission integer for auto-created directories.'],
                  ['create_dirs', 'bool', 'True', 'Auto-create root and parent directories on file write.'],
                ].map(([attr, type, defVal, desc], i) => (
                  <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                    <td className="py-3 px-6 font-mono text-xs font-semibold text-aquilia-400">{attr}</td>
                    <td className="py-3 px-6 font-mono text-xs">{type}</td>
                    <td className="py-3 px-6 font-mono text-xs">{defVal}</td>
                    <td className={`py-3 px-6 text-xs ${subtleText}`}>{desc}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* MemoryConfig */}
        <div className="mb-12">
          <h3 className={`text-xl font-bold mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
            <DocTerm id="storage.MemoryConfig">MemoryConfig</DocTerm>
          </h3>
          <p className={`text-sm mb-4 ${subtleText}`}>
            Configures ephemeral in-memory storage, useful for mocking disk I/O in test suites.
          </p>
          <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl mb-4">
            <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
              <thead>
                <tr className="border-b border-white/5 bg-white/5">
                  <th className="text-left py-3 px-6 font-semibold text-aquilia-500 w-44">Attribute</th>
                  <th className="text-left py-3 px-6">Type</th>
                  <th className="text-left py-3 px-6">Default</th>
                  <th className="text-left py-3 px-6">Description</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {[
                  ['max_size', 'int', '0', 'Maximum RAM limit in bytes. Set to 0 for unlimited.'],
                ].map(([attr, type, defVal, desc], i) => (
                  <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                    <td className="py-3 px-6 font-mono text-xs font-semibold text-aquilia-400">{attr}</td>
                    <td className="py-3 px-6 font-mono text-xs">{type}</td>
                    <td className="py-3 px-6 font-mono text-xs">{defVal}</td>
                    <td className={`py-3 px-6 text-xs ${subtleText}`}>{desc}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* S3Config */}
        <div className="mb-12">
          <h3 className={`text-xl font-bold mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
            <DocTerm id="storage.S3Config">S3Config</DocTerm>
          </h3>
          <p className={`text-sm mb-4 ${subtleText}`}>
            Configures AWS S3 and compatible storage layers.
          </p>
          <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl mb-4">
            <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
              <thead>
                <tr className="border-b border-white/5 bg-white/5">
                  <th className="text-left py-3 px-6 font-semibold text-aquilia-500 w-44">Attribute</th>
                  <th className="text-left py-3 px-6">Type</th>
                  <th className="text-left py-3 px-6">Default</th>
                  <th className="text-left py-3 px-6">Description</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {[
                  ['bucket', 'str', '""', 'S3 bucket name (required).'],
                  ['region', 'str', '"us-east-1"', 'Target AWS region.'],
                  ['access_key', 'str | None', 'None', 'AWS Access Key ID (uses boto3 chain if None).'],
                  ['secret_key', 'str | None', 'None', 'AWS Secret Access Key.'],
                  ['endpoint_url', 'str | None', 'None', 'Alternative endpoint URL (e.g. for MinIO, Spaces).'],
                  ['prefix', 'str', '""', 'Virtual directory prefix inside the bucket.'],
                  ['default_acl', 'str | None', 'None', 'Access control policy list (e.g. public-read).'],
                  ['presigned_expiry', 'int', '3600', 'Expires time in seconds for generated presigned URLs.'],
                ].map(([attr, type, defVal, desc], i) => (
                  <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                    <td className="py-3 px-6 font-mono text-xs font-semibold text-aquilia-400">{attr}</td>
                    <td className="py-3 px-6 font-mono text-xs">{type}</td>
                    <td className="py-3 px-6 font-mono text-xs">{defVal}</td>
                    <td className={`py-3 px-6 text-xs ${subtleText}`}>{desc}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* CompositeConfig */}
        <div className="mb-12">
          <h3 className={`text-xl font-bold mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
            <DocTerm id="storage.CompositeConfig">CompositeConfig</DocTerm>
          </h3>
          <p className={`text-sm mb-4 ${subtleText}`}>
            Configures composite storage to route calls dynamically to other backends.
          </p>
          <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl mb-4">
            <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
              <thead>
                <tr className="border-b border-white/5 bg-white/5">
                  <th className="text-left py-3 px-6 font-semibold text-aquilia-500 w-44">Attribute</th>
                  <th className="text-left py-3 px-6">Type</th>
                  <th className="text-left py-3 px-6">Default</th>
                  <th className="text-left py-3 px-6">Description</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {[
                  ['backends', 'dict', '{}', 'Sub-backend dictionary mappings.'],
                  ['rules', 'dict', '{}', 'Glob patterns mapped to target backend aliases.'],
                  ['fallback', 'str', '"default"', 'Alias to route requests to when no rules match.'],
                ].map(([attr, type, defVal, desc], i) => (
                  <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                    <td className="py-3 px-6 font-mono text-xs font-semibold text-aquilia-400">{attr}</td>
                    <td className="py-3 px-6 font-mono text-xs">{type}</td>
                    <td className="py-3 px-6 font-mono text-xs">{defVal}</td>
                    <td className={`py-3 px-6 text-xs ${subtleText}`}>{desc}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Module Level Manifest Configuration */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Module Manifest & ComponentRef
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Instead of declaring component imports as bare string paths, Aquilia v2 recommends using the <code className="text-aquilia-500">ComponentRef</code> class inside <code className="text-aquilia-500">manifest.py</code>. This offers typed metadata checks during boot scans.
        </p>

        <CodeBlock language="python" highlightLines={[8, 9, 10, 11]}>{`# modules/uploads/manifest.py
from aquilia import AppManifest, ComponentRef, ComponentKind

manifest = AppManifest(
    name="uploads",
    controllers=[
        # Controller component references
        ComponentRef(
            class_path="modules.uploads.controllers:FilesController",
            kind=ComponentKind.CONTROLLER
        )
    ],
    services=[]
)`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
