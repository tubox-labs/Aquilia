import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { NextSteps } from '../../../components/NextSteps'
import { Terminal, ShieldAlert } from 'lucide-react'

const commands: [string, string, string][] = [
  ['aq vectordb status', '--json', 'Driver availability, declared stores, resolved paths. Reads config only — takes no lock.'],
  ['aq vectordb gpu', '-s/--store, --json', 'Probes GPU capability and shows the resolved policy per store.'],
  ['aq vectordb models', '--json', 'Registered models with their slot routing, collection, store and dimension.'],
  ['aq vectordb inspect [STORE]', '--json', 'Opens each store and reports live health.'],
  ['aq vectordb stats [STORE]', '--json', 'Per-collection record counts, tombstones, codec, WAL depth.'],
  ['aq vectordb compact [STORE]', '', 'Reclaims space held by deleted records.'],
  ['aq vectordb vacuum [STORE]', '', 'Releases free pages back to the filesystem.'],
  ['aq vectordb compress [STORE]', '--codec, --sample-size, --pq-dim, --pq-bits, --yes', 'Trains a quantization codebook and compresses in place.'],
  ['aq vectordb reindex MODEL', '-b/--batch-size', 'Rebuilds a mirrored collection from its SQL table.'],
  ['aq vectordb reembed', '-m/--model, --to-embedder, -b/--batch-size, --dry-run', 'Re-embeds a collection under a different embedding model.'],
]

export function VectorDBCli() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Terminal className="w-4 h-4 animate-pulse" />
          Vector Database / CLI
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          aq vectordb
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          New in 1.4.0b3. Ten subcommands for inspecting and maintaining vector stores. The group is
          filed under <strong>Database</strong> in <code className="text-aquilia-500">aq --help</code>,
          next to <code className="text-aquilia-500">aq db</code>.
        </p>
      </div>

      {/* Command table */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Command reference
        </h2>
        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="text-left py-4 px-6 font-semibold text-aquilia-500">Command</th>
                <th className="text-left py-4 px-6 font-semibold">Flags</th>
                <th className="text-left py-4 px-6 font-semibold">Purpose</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {commands.map(([cmd, flags, desc], i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                  <td className="py-3.5 px-6 font-mono text-xs text-aquilia-400 whitespace-nowrap align-top">{cmd}</td>
                  <td className={`py-3.5 px-6 font-mono text-xs align-top ${subtleText}`}>{flags || '—'}</td>
                  <td className={`py-3.5 px-6 text-xs ${subtleText}`}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className={`mt-4 text-sm ${subtleText}`}>
          Every read-only command takes <code className="text-aquilia-500">--json</code> so a CI job
          or dashboard can consume the same output a human reads.{' '}
          <code className="text-aquilia-500">compact</code>,{' '}
          <code className="text-aquilia-500">vacuum</code> and{' '}
          <code className="text-aquilia-500">compress</code> refuse to run against a store declared{' '}
          <code className="text-aquilia-500">read_only</code>.
        </p>
      </section>

      {/* Workflows */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Common workflows
        </h2>

        <h3 className={`text-sm font-bold mb-2 mt-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Confirm the install before a deploy</h3>
        <CodeBlock language="bash">{`aq vectordb status          # driver present? stores resolvable?
aq doctor                   # includes the vectordb.driver check
aq vectordb models          # do the registered models route slots as you expect?`}</CodeBlock>

        <h3 className={`text-sm font-bold mb-2 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>Reclaim space after a bulk delete</h3>
        <CodeBlock language="bash">{`aq vectordb stats default   # check tombstone_ratio
aq vectordb compact default # reclaim space held by deleted records
aq vectordb vacuum default  # release free pages to the filesystem
aq vectordb stats default   # confirm`}</CodeBlock>

        <h3 className={`text-sm font-bold mb-2 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>Swap the embedder</h3>
        <CodeBlock language="bash">{`# Dry run first — reports how many records would change, writes nothing.
aq vectordb reembed --model Document \\
  --to-embedder openai/text-embedding-3-large --dry-run

# Apply. Vectors are written back under the same keys, so payloads and
# SQL links survive. Records with no stored text are counted and reported
# rather than silently left on the old model.
aq vectordb reembed --model Document \\
  --to-embedder openai/text-embedding-3-large`}</CodeBlock>
        <p className={`mt-3 text-sm ${subtleText}`}>
          A dimension change cannot be applied in place — elips holds dimension database-global, so
          the command refuses and names the store to reconfigure rather than writing vectors the
          index cannot use.
        </p>

        <h3 className={`text-sm font-bold mb-2 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>Rebuild vectors from SQL rows</h3>
        <CodeBlock language="bash">{`# For a model mirrored from an ORM table — re-reads rows and rewrites vectors.
aq vectordb reindex Article --batch-size 500`}</CodeBlock>
      </section>

      {/* Writer lock warning */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <ShieldAlert className="w-5 h-5 text-amber-500" />
          Run maintenance against a stopped app
        </h2>
        <div className={`rounded-xl border p-5 ${isDark ? 'border-amber-500/20 bg-amber-500/5' : 'border-amber-300 bg-amber-50'}`}>
          <p className={`text-sm mb-3 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <code className="text-aquilia-500">elips</code> is embedded and single-writer per store
            directory. <code className="text-aquilia-500">inspect</code>,{' '}
            <code className="text-aquilia-500">stats</code>,{' '}
            <code className="text-aquilia-500">compact</code>,{' '}
            <code className="text-aquilia-500">vacuum</code>,{' '}
            <code className="text-aquilia-500">compress</code>,{' '}
            <code className="text-aquilia-500">reindex</code> and{' '}
            <code className="text-aquilia-500">reembed</code> all open the store and take that lock,
            so they fail while a server holds the same path. That is the lock working, not a bug —
            use <code className="text-aquilia-500">aq vectordb status</code>, which opens nothing,
            against a live deployment.
          </p>
          <p className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <code className="text-aquilia-500">compress</code> is not reversible in place. Training
            the codebook frees the full-precision vectors, so restoring them means re-ingesting or
            re-embedding. The confirmation prompt exists for that reason; back up the store
            directory before scripting it with <code className="text-aquilia-500">--yes</code>.
          </p>
        </div>
      </section>

      {/* Compression */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Compression trade-off
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Three codecs. <code className="text-aquilia-500">sq8</code> stores one byte per dimension,
          roughly 4× smaller. <code className="text-aquilia-500">pq</code> and{' '}
          <code className="text-aquilia-500">opq</code> store a short code per vector, 8–32× smaller.
          Distances become approximate, which is why every hit afterwards carries{' '}
          <code className="text-aquilia-500">approximate=True</code> and its codec name.
        </p>
        <CodeBlock language="bash">{`aq vectordb compress default --codec sq8       # ~4x smaller, mildest recall cost
aq vectordb compress default --codec pq --pq-dim 96 --pq-bits 8
aq vectordb stats default                      # confirm the codec and size`}</CodeBlock>
        <p className={`mt-3 mb-4 text-sm ${subtleText}`}>
          <code className="text-aquilia-500">--sample-size</code> (default 10000) controls how many
          vectors train the codebook. <code className="text-aquilia-500">--yes</code> skips the
          confirmation prompt for scripted runs.
        </p>
        <CodeBlock language="python">{`hits = await Document.vectors.search("query text", limit=10)

for hit in hits:
    if hit.approximate:
        # Distance came from a reconstructed vector — treat the score as an estimate
        print(hit.score, hit.codec)`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
