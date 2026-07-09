import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { NextSteps } from '../../../components/NextSteps'
import { Archive } from 'lucide-react'

export function CLIArtifactCommands() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const sectionClass = "mb-16 scroll-mt-24"
  const h2Class = `text-2xl font-bold mb-6 flex items-center gap-3 ${isDark ? 'text-white' : 'text-gray-900'}`
  const h3Class = `text-lg font-semibold mt-8 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`
  const pClass = `mb-4 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`

  return (
    <div className="max-w-4xl mx-auto pb-20">
      {/* Header */}
      <div className="mb-12 border-b border-gray-200 dark:border-white/10 pb-8">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Archive className="w-4 h-4" />
          CLI / Artifacts
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Artifact Commands
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500 font-mono font-bold">aq artifact</code> command group coordinates build registries, verifies signatures, and manages compiled releases.
        </p>
      </div>

      {/* aq artifact list */}
      <section id="artifact-list" className={sectionClass}>
        <h2 className={h2Class}>aq artifact list</h2>
        <p className={pClass}>
          Lists built artifacts inside the store folder, with options to filter by tags or kind type.
        </p>
        <CodeBlock language="bash" filename="Terminal">{`# List all artifacts in default directory
aq artifact list

# Filter to show only compiled route model artifacts
aq artifact list --kind=routes --tag=env=prod`}</CodeBlock>

        <h3 className={h3Class}>Options</h3>
        <div className="overflow-x-auto py-2 mb-6">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400 text-left">
                <th className="px-4 py-3 font-semibold">Option</th>
                <th className="px-4 py-3 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5 text-gray-300' : 'divide-gray-150 text-gray-700'}`}>
              {[
                ['--kind, -k', 'Filter by artifact type (routes, di, templates, translations).'],
                ['--tag, -t', 'Filter by custom tags key-value pairs.'],
                ['--dir, -d', 'Custom artifact registry target directory.']
              ].map(([opt, desc], i) => (
                <tr key={i} className="hover:bg-aquilia-500/5 transition-colors">
                  <td className="px-4 py-2 font-mono text-xs text-aquilia-500 font-semibold">{opt}</td>
                  <td className="px-4 py-2 text-xs">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* aq artifact inspect */}
      <section id="artifact-inspect" className={sectionClass}>
        <h2 className={h2Class}>aq artifact inspect</h2>
        <p className={pClass}>
          Dumps raw metadata, digital signatures, and target files compiled within the designated `.surp` archive.
        </p>
        <CodeBlock language="bash" filename="Terminal">aq artifact inspect package-id-abc</CodeBlock>
      </section>

      {/* aq artifact verify */}
      <section id="artifact-verify" className={sectionClass}>
        <h2 className={h2Class}>aq artifact verify</h2>
        <p className={pClass}>
          Computes hashes and checks cryptographic signatures on compiled artifacts to ensure they match deployment records.
        </p>
        <CodeBlock language="bash" filename="Terminal">{`# Verify single artifact integrity
aq artifact verify package-id-abc

# Batch verify all files in registry
aq artifact verify-all`}</CodeBlock>
      </section>

      {/* aq artifact gc */}
      <section id="artifact-gc" className={sectionClass}>
        <h2 className={h2Class}>aq artifact gc</h2>
        <p className={pClass}>
          Garbage collects unreferenced files or stale release bundles to free up storage space.
        </p>
        <CodeBlock language="bash" filename="Terminal">aq artifact gc --days-older-than=30</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
