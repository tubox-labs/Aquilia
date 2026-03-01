import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Terminal, Archive } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function CLIArtifactCommands() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const sectionClass = 'mb-16 scroll-mt-24'
  const h2Class = `text-2xl font-bold mb-6 flex items-center gap-3 ${isDark ? 'text-white' : 'text-gray-900'}`
  const h3Class = `text-lg font-semibold mt-8 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`
  const pClass = `mb-4 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`
  const codeClass = 'text-xs font-mono bg-black/5 dark:bg-white/10 px-1.5 py-0.5 rounded text-aquilia-600 dark:text-aquilia-400'

  const Table = ({ children }: { children: React.ReactNode }) => (
    <div className={`overflow-hidden border rounded-lg mb-6 ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
      <table className="w-full text-sm text-left">
        <thead className={`text-xs uppercase ${isDark ? 'bg-white/5 text-gray-400' : 'bg-gray-50 text-gray-500'}`}>
          <tr>
            <th className="px-4 py-3 font-medium">Option</th>
            <th className="px-4 py-3 font-medium">Description</th>
            <th className="px-4 py-3 font-medium w-32">Default</th>
          </tr>
        </thead>
        <tbody className={`divide-y ${isDark ? 'divide-white/10' : 'divide-gray-200'}`}>
          {children}
        </tbody>
      </table>
    </div>
  )

  const Row = ({ opt, desc, def: defaultVal }: { opt: string; desc: string; def?: string }) => (
    <tr className={isDark ? 'hover:bg-white/5' : 'hover:bg-gray-50'}>
      <td className="px-4 py-3 font-mono text-aquilia-500">{opt}</td>
      <td className={`px-4 py-3 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>{desc}</td>
      <td className={`px-4 py-3 font-mono text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>{defaultVal || '-'}</td>
    </tr>
  )

  return (
    <div className="max-w-4xl mx-auto pb-20">
      {/* Header */}
      <div className="mb-12 border-b border-gray-200 dark:border-white/10 pb-8">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Archive className="w-4 h-4" />
          CLI / Artifact Commands
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Artifact Commands
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className={codeClass}>aq artifact</code> command group provides full lifecycle management for content-addressed, provenance-tracked artifacts — list, inspect, verify, export, diff, and garbage collect.
        </p>
      </div>

      {/* Overview */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Archive className="w-6 h-6 text-aquilia-500" />
          Sub-Commands
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {[
            { cmd: 'aq artifact list', desc: 'List all artifacts in the store with optional kind/tag filtering' },
            { cmd: 'aq artifact inspect', desc: 'Show full metadata, provenance, tags, and payload preview for an artifact' },
            { cmd: 'aq artifact verify', desc: 'Verify the SHA-256 integrity of a single artifact' },
            { cmd: 'aq artifact verify-all', desc: 'Batch-verify integrity of ALL artifacts in the store' },
            { cmd: 'aq artifact gc', desc: 'Garbage-collect unreferenced artifacts' },
            { cmd: 'aq artifact export', desc: 'Export artifacts as a portable JSON bundle' },
            { cmd: 'aq artifact diff', desc: 'Show differences between two versions of an artifact' },
            { cmd: 'aq artifact history', desc: 'Show version history for an artifact' },
            { cmd: 'aq artifact import', desc: 'Import artifacts from a previously exported bundle' },
            { cmd: 'aq artifact count', desc: 'Count artifacts in the store with optional kind filter' },
            { cmd: 'aq artifact stats', desc: 'Show aggregate statistics across all artifacts' },
          ].map((item, i) => (
            <div key={i} className={boxClass}>
              <code className={`font-bold text-sm ${isDark ? 'text-aquilia-400' : 'text-aquilia-600'}`}>{item.cmd}</code>
              <p className={`text-xs mt-1 ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* artifact list */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Terminal className="w-6 h-6 text-aquilia-500" />
          aq artifact list
        </h2>
        <p className={pClass}>
          List all artifacts in the <code className={codeClass}>FilesystemArtifactStore</code> with optional filters by kind and tag.
        </p>
        <Table>
          <Row opt="--dir, -d" desc="Artifact store directory" def="artifacts" />
          <Row opt="--kind, -k" desc="Filter by artifact kind (e.g. model, config, workspace)" def="all" />
          <Row opt="--tag, -t" desc="Filter by tag in key=value format" def="-" />
          <Row opt="--json-output, -j" desc="Output as JSON instead of table" def="false" />
        </Table>
        <CodeBlock language="bash" filename="Terminal">{`# List all artifacts
aq artifact list

# Filter by kind
aq artifact list --kind model

# Filter by tag
aq artifact list --tag env=production

# JSON output
aq artifact list -j

# Custom store directory
aq artifact list --dir ./build/artifacts`}</CodeBlock>
      </section>

      {/* artifact inspect */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Terminal className="w-6 h-6 text-aquilia-500" />
          aq artifact inspect
        </h2>
        <p className={pClass}>
          Show detailed metadata for a specific artifact including kind, digest, creation timestamp, creator, git SHA, hostname, tags, metadata keys, and a payload preview.
        </p>
        <Table>
          <Row opt="NAME" desc="Artifact name (positional argument)" def="-" />
          <Row opt="--version, -V" desc="Specific version to inspect" def="latest" />
          <Row opt="--dir, -d" desc="Artifact store directory" def="artifacts" />
          <Row opt="--json-output, -j" desc="Output as JSON" def="false" />
        </Table>
        <CodeBlock language="bash" filename="Terminal">{`# Inspect an artifact
aq artifact inspect my-config

# Inspect specific version
aq artifact inspect my-model --version v1.0.0

# JSON output
aq artifact inspect my-model -j`}</CodeBlock>
      </section>

      {/* artifact verify */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Terminal className="w-6 h-6 text-aquilia-500" />
          aq artifact verify
        </h2>
        <p className={pClass}>
          Verify the SHA-256 content integrity of a single artifact. Returns exit code 0 on success, 1 on failure.
        </p>
        <Table>
          <Row opt="NAME" desc="Artifact name (positional argument)" def="-" />
          <Row opt="--version, -V" desc="Specific version to verify" def="latest" />
          <Row opt="--dir, -d" desc="Artifact store directory" def="artifacts" />
        </Table>
        <CodeBlock language="bash" filename="Terminal">{`# Verify integrity
aq artifact verify my-config

# Verify specific version
aq artifact verify my-model --version v1.0.0`}</CodeBlock>
      </section>

      {/* artifact verify-all */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Terminal className="w-6 h-6 text-aquilia-500" />
          aq artifact verify-all
        </h2>
        <p className={pClass}>
          Batch-verify the integrity of every artifact in the store. Reports passed/failed counts and lists any failed artifact names.
        </p>
        <Table>
          <Row opt="--dir, -d" desc="Artifact store directory" def="artifacts" />
          <Row opt="--json-output, -j" desc="Output as JSON" def="false" />
        </Table>
        <CodeBlock language="bash" filename="Terminal">{`# Verify all artifacts
aq artifact verify-all

# JSON output
aq artifact verify-all -j`}</CodeBlock>
      </section>

      {/* artifact gc */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Terminal className="w-6 h-6 text-aquilia-500" />
          aq artifact gc
        </h2>
        <p className={pClass}>
          Garbage-collect unreferenced artifacts from the store. Optionally keep specific artifacts by their digest.
        </p>
        <Table>
          <Row opt="--dir, -d" desc="Artifact store directory" def="artifacts" />
          <Row opt="--keep, -k" desc="Digests to keep (repeatable)" def="-" />
          <Row opt="--dry-run" desc="Show what would be removed without deleting" def="false" />
        </Table>
        <CodeBlock language="bash" filename="Terminal">{`# Garbage collect
aq artifact gc

# Keep specific digests
aq artifact gc --keep sha256:abc123 --keep sha256:def456

# Preview what would be removed
aq artifact gc --dry-run`}</CodeBlock>
      </section>

      {/* artifact export */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Terminal className="w-6 h-6 text-aquilia-500" />
          aq artifact export
        </h2>
        <p className={pClass}>
          Export artifacts as a portable JSON bundle file. Useful for transferring artifacts between environments or creating release bundles.
        </p>
        <Table>
          <Row opt="--dir, -d" desc="Artifact store directory" def="artifacts" />
          <Row opt="--output, -o" desc="Output bundle file path" def="bundle.aq.json" />
          <Row opt="--name, -n" desc="Specific artifact names to export (repeatable)" def="all" />
        </Table>
        <CodeBlock language="bash" filename="Terminal">{`# Export specific artifacts
aq artifact export --name my-config --name my-model -o release.aq.json

# Export all artifacts
aq artifact export`}</CodeBlock>
      </section>

      {/* artifact diff */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Terminal className="w-6 h-6 text-aquilia-500" />
          aq artifact diff
        </h2>
        <p className={pClass}>
          Show differences between two versions of the same artifact. Compares metadata, tags, and payload content. Useful for understanding what changed between releases.
        </p>
        <Table>
          <Row opt="NAME" desc="Artifact name (positional argument)" def="-" />
          <Row opt="VERSION_A" desc="First version to compare (positional argument)" def="-" />
          <Row opt="VERSION_B" desc="Second version to compare (positional argument)" def="-" />
          <Row opt="--dir, -d" desc="Artifact store directory" def="artifacts" />
        </Table>
        <CodeBlock language="bash" filename="Terminal">{`# Diff two versions
aq artifact diff my-config 1.0.0 1.1.0

# Diff from custom store directory
aq artifact diff my-model 2.0.0 2.1.0 --dir ./build/artifacts`}</CodeBlock>
      </section>

      {/* artifact history */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Terminal className="w-6 h-6 text-aquilia-500" />
          aq artifact history
        </h2>
        <p className={pClass}>
          Show version history for a specific artifact. Lists all versions with their creation timestamp, digest, kind, and tags.
        </p>
        <Table>
          <Row opt="NAME" desc="Artifact name (positional argument)" def="-" />
          <Row opt="--dir, -d" desc="Artifact store directory" def="artifacts" />
        </Table>
        <CodeBlock language="bash" filename="Terminal">{`# Show version history
aq artifact history my-model

# Custom directory
aq artifact history my-config --dir ./build/artifacts`}</CodeBlock>
      </section>

      {/* artifact import */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Terminal className="w-6 h-6 text-aquilia-500" />
          aq artifact import
        </h2>
        <p className={pClass}>
          Import artifacts from a previously exported JSON bundle into the local artifact store. The inverse of <code className={codeClass}>aq artifact export</code>.
        </p>
        <Table>
          <Row opt="BUNDLE_PATH" desc="Path to the exported bundle file (positional argument)" def="-" />
          <Row opt="--dir, -d" desc="Target artifact store directory" def="artifacts" />
        </Table>
        <CodeBlock language="bash" filename="Terminal">{`# Import from a bundle
aq artifact import release.aq.json

# Import into custom directory
aq artifact import bundle.aq.json --dir ./build/artifacts`}</CodeBlock>
      </section>

      {/* artifact count */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Terminal className="w-6 h-6 text-aquilia-500" />
          aq artifact count
        </h2>
        <p className={pClass}>
          Count the total number of artifacts in the store, optionally filtered by kind.
        </p>
        <Table>
          <Row opt="--dir, -d" desc="Artifact store directory" def="artifacts" />
          <Row opt="--kind, -k" desc="Filter by artifact kind (e.g. model, config, workspace)" def="all" />
        </Table>
        <CodeBlock language="bash" filename="Terminal">{`# Count all artifacts
aq artifact count

# Count by kind
aq artifact count --kind model
aq artifact count --kind config`}</CodeBlock>
      </section>

      {/* artifact stats */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Terminal className="w-6 h-6 text-aquilia-500" />
          aq artifact stats
        </h2>
        <p className={pClass}>
          Show aggregate statistics across all artifacts in the store — total count, count by kind, total size, latest activity, and more.
        </p>
        <Table>
          <Row opt="--dir, -d" desc="Artifact store directory" def="artifacts" />
          <Row opt="--json-output, -j" desc="Output as JSON" def="false" />
        </Table>
        <CodeBlock language="bash" filename="Terminal">{`# Show stats
aq artifact stats

# JSON output
aq artifact stats -j`}</CodeBlock>
      </section>

      {/* Artifact System Architecture */}
      <section className={sectionClass}>
        <h2 className={h2Class}>Artifact System Architecture</h2>
        <p className={pClass}>
          Aquilia's artifact system is content-addressed and provenance-tracked. Every artifact includes:
        </p>
        <ul className={`list-disc pl-6 mb-4 space-y-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <li><strong>Name + Version</strong> — semantic identification</li>
          <li><strong>Kind</strong> — type classification (workspace, registry, route, di-graph, config, code, model)</li>
          <li><strong>SHA-256 Digest</strong> — content-addressed integrity verification</li>
          <li><strong>Provenance</strong> — creator, hostname, git SHA, creation timestamp</li>
          <li><strong>Tags</strong> — key-value metadata for filtering and organization</li>
          <li><strong>Payload</strong> — the actual artifact content (JSON, binary, etc.)</li>
        </ul>
        <CodeBlock language="text" filename="Artifact Flow">{`aq compile  ──▶  aq artifact list  ──▶  aq artifact verify
    │                                          │
    ▼                                          ▼
aq freeze  ──▶  aq artifact export  ──▶  Production Deploy`}</CodeBlock>
      </section>

      <NextSteps
        items={[
          { text: 'Core Commands', link: '/docs/cli/core' },
          { text: 'Deploy Commands', link: '/docs/cli/deploy' },
          { text: 'Trace Commands', link: '/docs/cli/trace' },
          { text: 'Aquilary Registry', link: '/docs/aquilary' },
        ]}
      />
    </div>
  )
}
