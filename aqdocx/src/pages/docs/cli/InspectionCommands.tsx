import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Info, Search, FileSearch, BarChart3, Compass } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function CLIInspectionCommands() {
    const { theme } = useTheme()
    const isDark = theme === 'dark'

    // Styles
    const sectionClass = "mb-16 scroll-mt-24"
    const h2Class = `text-2xl font-bold mb-6 flex items-center gap-3 ${isDark ? 'text-white' : 'text-gray-900'}`
    const h3Class = `text-lg font-semibold mt-8 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`
    const pClass = `mb-4 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`
    const codeClass = "text-xs font-mono bg-black/5 dark:bg-white/10 px-1.5 py-0.5 rounded text-aquilia-600 dark:text-aquilia-400"
    const boxClass = `rounded-xl border p-6 mb-8 ${isDark ? 'bg-white/[0.02] border-white/10' : 'bg-gray-50/50 border-gray-200'}`

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

    const Row = ({ opt, desc, def }: { opt: string, desc: string, def?: string }) => (
        <tr className={isDark ? 'hover:bg-white/5' : 'hover:bg-gray-50'}>
            <td className="px-4 py-3 font-mono text-aquilia-500">{opt}</td>
            <td className={`px-4 py-3 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>{desc}</td>
            <td className={`px-4 py-3 font-mono text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>{def || '-'}</td>
        </tr>
    )

    return (
        <div className="max-w-4xl mx-auto pb-20">
            {/* Header */}
            <div className="mb-12 border-b border-gray-200 dark:border-white/10 pb-8">
                <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
                    <Info className="w-4 h-4" />
                    CLI / Inspection & Discovery
                </div>
                <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
                  <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
                    Inspection & Discovery
                    <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
                  </span>
                </h1>
                <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                    Static analysis tools for inspecting compiled workspace state, managing module manifests, discovering components, and generating analytics reports — all without starting the server.
                </p>
            </div>

            {/* Overview grid */}
            <div className={boxClass}>
                <h3 className={`text-sm font-semibold uppercase tracking-wider mb-4 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                    Commands in this group
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {[
                        { cmd: 'inspect', desc: 'Static introspection' },
                        { cmd: 'manifest', desc: 'Manifest management' },
                        { cmd: 'discover', desc: 'Component discovery' },
                        { cmd: 'analytics', desc: 'Health report' },
                    ].map(({ cmd, desc }) => (
                        <a key={cmd} href={`#${cmd}`} className={`rounded-lg border px-3 py-2 text-center transition-colors ${isDark ? 'border-white/10 hover:bg-white/5' : 'border-gray-200 hover:bg-gray-50'}`}>
                            <span className="block font-mono text-sm text-aquilia-500">{cmd}</span>
                            <span className={`block text-xs mt-0.5 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>{desc}</span>
                        </a>
                    ))}
                </div>
            </div>

            {/* Inspect */}
            <section id="inspect" className={sectionClass}>
                <h2 className={h2Class}><Search className="w-6 h-6 text-aquilia-500" /> Static Inspection — aq inspect</h2>
                <p className={pClass}>
                    The <span className={codeClass}>inspect</span> group reveals the compiled state of your application without running it.
                    It loads module manifests and analyses controllers, services, fault domains, routes, and configuration files.
                    Pass <span className={codeClass}>--verbose / -v</span> at the root level for detailed output.
                </p>

                <h3 className={h3Class}>inspect routes</h3>
                <p className={pClass}>
                    List all compiled URI routes and their handler references. Scans every module's manifest, discovers controllers,
                    and resolves <span className={codeClass}>__controller_routes__</span> or <span className={codeClass}>__route__</span> decorator metadata.
                </p>
                <CodeBlock language="bash" filename="terminal">aq inspect routes</CodeBlock>

                <h3 className={h3Class}>inspect di</h3>
                <p className={pClass}>
                    Visualise the Dependency Injection service graph. Lists every registered service with its scope (<span className={codeClass}>app</span>, <span className={codeClass}>request</span>, etc.) and import path.
                </p>
                <CodeBlock language="bash" filename="terminal">aq inspect di</CodeBlock>

                <h3 className={h3Class}>inspect modules</h3>
                <p className={pClass}>
                    List all detected modules in a table showing name, version, route prefix, controller count, and service count.
                    With <span className={codeClass}>-v</span>, also shows description, author, tags, and dependencies.
                </p>
                <CodeBlock language="bash" filename="terminal">{`aq inspect modules
aq -v inspect modules`}</CodeBlock>

                <h3 className={h3Class}>inspect faults</h3>
                <p className={pClass}>
                    Show fault domain boundaries per module, including default domain name, propagation strategy, and registered fault handlers.
                </p>
                <CodeBlock language="bash" filename="terminal">aq inspect faults</CodeBlock>

                <h3 className={h3Class}>inspect config</h3>
                <p className={pClass}>
                    Show fully resolved configuration: workspace file path, config directory contents (YAML), and any <span className={codeClass}>AQUILIA_*</span> environment variables.
                    With <span className={codeClass}>-v</span>, prints the full contents of each config file.
                </p>
                <CodeBlock language="bash" filename="terminal">{`aq inspect config
aq -v inspect config`}</CodeBlock>
            </section>

            {/* Manifest */}
            <section id="manifest" className={sectionClass}>
                <h2 className={h2Class}><FileSearch className="w-6 h-6 text-indigo-500" /> Manifest Management — aq manifest</h2>
                <p className={pClass}>
                    Synchronise auto-discovered resources (controllers, services) into module <span className={codeClass}>manifest.py</span> files.
                    Uses AST-level parsing and rewriting to preserve comments and formatting.
                </p>

                <h3 className={h3Class}>manifest update</h3>
                <p className={pClass}>
                    Scan a module for controllers and services, then write them explicitly into <span className={codeClass}>manifest.py</span>.
                </p>
                <CodeBlock language="bash" filename="terminal">
                    aq manifest update MODULE [OPTIONS]
                </CodeBlock>
                <Table>
                    <Row opt="MODULE" desc="Module name to update (positional, required)" />
                    <Row opt="--check" desc="Fail if manifest is out of sync — CI mode (exit 1 on diff)" def="false" />
                    <Row opt="--freeze" desc="Disable auto-discovery after sync — strict / production mode" def="false" />
                </Table>
                <CodeBlock language="bash" filename="terminal">{`# Normal sync
aq manifest update users

# CI gate — fail if out of sync
aq manifest update users --check

# Lock manifest for production
aq manifest update users --freeze`}</CodeBlock>
            </section>

            {/* Discover */}
            <section id="discover" className={sectionClass}>
                <h2 className={h2Class}><Compass className="w-6 h-6 text-green-500" /> Discovery — aq discover</h2>
                <p className={pClass}>
                    Scan the workspace to discover all modules, controllers, and services without modifying any files.
                    Optionally auto-sync discovered components into <span className={codeClass}>manifest.py</span> files.
                </p>
                <CodeBlock language="bash" filename="terminal">
                    aq discover [OPTIONS]
                </CodeBlock>
                <Table>
                    <Row opt="--path" desc="Workspace path to scan" def="." />
                    <Row opt="--sync" desc="Auto-sync discovered components into manifest.py files" def="false" />
                    <Row opt="--dry-run" desc="Preview sync changes without writing (use with --sync)" def="false" />
                </Table>
                <CodeBlock language="bash" filename="terminal">{`aq discover
aq discover --path /app
aq discover --sync --dry-run
aq discover --sync`}</CodeBlock>
            </section>

            {/* Analytics */}
            <section id="analytics" className={sectionClass}>
                <h2 className={h2Class}><BarChart3 className="w-6 h-6 text-blue-500" /> Analytics — aq analytics</h2>
                <p className={pClass}>
                    Run a full discovery analysis and print a workspace health report covering module count, route coverage, service registration, and potential issues.
                </p>
                <CodeBlock language="bash" filename="terminal">
                    aq analytics [OPTIONS]
                </CodeBlock>
                <Table>
                    <Row opt="--path" desc="Workspace path to analyse" def="." />
                </Table>
                <CodeBlock language="bash" filename="terminal">{`aq analytics
aq analytics --path /app`}</CodeBlock>
            </section>

            {/* Cross-references */}
            <section className={sectionClass}>
                <h2 className={`text-xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Related Pages</h2>
                <p className={pClass}>
                    Dedicated documentation for subsystems, trace, artifacts, and WebSocket commands is available on their own pages:
                </p>
                <ul className={`space-y-2 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                    <li>• <a href="/docs/cli/trace" className="text-aquilia-500 hover:underline">Trace Commands</a> — <span className={codeClass}>aq trace status | journal | diff | export | clean</span></li>
                    <li>• <a href="/docs/cli/artifacts" className="text-aquilia-500 hover:underline">Artifact Commands</a> — <span className={codeClass}>aq artifact list | inspect | verify | gc | export | diff | history | import | count | stats</span></li>
                    <li>• <a href="/docs/cli/websocket" className="text-aquilia-500 hover:underline">WebSocket Commands</a> — <span className={codeClass}>aq ws inspect | broadcast | gen-client | rooms | kick</span></li>
                    <li>• <a href="/docs/cli/subsystems" className="text-aquilia-500 hover:underline">Subsystem Commands</a> — <span className={codeClass}>aq cache | mail</span> and more</li>
                </ul>
            </section>
        
      <NextSteps />
    </div>
    )
}