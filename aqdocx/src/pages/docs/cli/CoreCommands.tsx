import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Terminal } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function CLICoreCommands() {
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
          <Terminal className="w-4 h-4" />
          CLI / Core Commands
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Core Commands
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Core lifecycle commands handle workspace bootstrap, module configurations, manifest validations, asset compilation, and server execution.
        </p>
      </div>

      {/* aq init workspace */}
      <section id="init" className={sectionClass}>
        <h2 className={h2Class}><DocTerm id="cli.init_workspace">aq init workspace</DocTerm></h2>
        <p className={pClass}>
          Creates a new workspace structure. Generates the base <code className="text-aquilia-500 font-mono">workspace.py</code>, the entrypoint module, and configuration folders.
        </p>
        <CodeBlock language="bash" filename="Terminal" highlightLines={[2, 5]}>{`# Initialize standard API project
aq init workspace billing-api --template=api

# Initialize minimal workspace without examples
aq init workspace core-service --minimal --yes`}</CodeBlock>

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
                ['--minimal', 'Creates absolute minimal structure: workspace.py and empty modules folder.'],
                ['--template', 'Scaffolding starting template: api (default), service, monolith.'],
                ['--yes, -y', 'Automatically answers yes to prompts, creating directories and over-writing contents safely.']
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

      {/* aq add module */}
      <section id="add" className={sectionClass}>
        <h2 className={h2Class}><DocTerm id="cli.add_module">aq add module</DocTerm></h2>
        <p className={pClass}>
          Generates a new self-contained module directory inside <code className="text-aquilia-500 font-mono">modules/</code>, creating a default <code className="text-aquilia-500 font-mono">manifest.py</code>, controller, models, and tests files.
        </p>
        <CodeBlock language="bash" filename="Terminal" highlightLines={[2, 5]}>{`# Standard module scaffold
aq add module auth

# Custom route prefix and module dependency declarations
aq add module payments --depends-on=users --depends-on=auth --route-prefix=/v2/pay`}</CodeBlock>

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
                ['--depends-on', 'Declare dependency on another module. Can be repeated multiple times.'],
                ['--fault-domain', 'Define a custom fault isolation domain for error scoping.'],
                ['--route-prefix', 'Injects a customized routing prefix for the module\'s endpoints.'],
                ['--with-tests', 'Appends a test file structure inside the generated module folder.'],
                ['--minimal', 'Creates only a manifest.py and controller file, skipping database models.'],
                ['--no-docker', 'Tells the generator not to auto-update the main Dockerfile with the new module.']
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

      {/* aq validate */}
      <section id="validate" className={sectionClass}>
        <h2 className={h2Class}><DocTerm id="cli.validate">aq validate</DocTerm></h2>
        <p className={pClass}>
          Parses workspace manifests statically, checking that dependency graphs are clear of cycles and routes do not overlap.
        </p>
        <CodeBlock language="bash" filename="Terminal" highlightLines={[2, 5]}>{`# Validate entire workspace
aq validate

# Run validation and output details in JSON format
aq validate --strict --json`}</CodeBlock>
      </section>

      {/* aq compile */}
      <section id="compile" className={sectionClass}>
        <h2 className={h2Class}><DocTerm id="cli.compile">aq compile</DocTerm></h2>
        <p className={pClass}>
          Compiles modular controllers, routers, blueprints, and translations into a compiled directory of static `.surp` files. This is recommended before deploying to production.
        </p>
        <CodeBlock language="bash" filename="Terminal" highlightLines={[2, 5]}>{`# Run compilation
aq compile

# Watch the workspace for edits and automatically recompile files
aq compile --watch --output=dist/`}</CodeBlock>
      </section>

      {/* aq run */}
      <section id="run" className={sectionClass}>
        <h2 className={h2Class}><DocTerm id="cli.run">aq run</DocTerm></h2>
        <p className={pClass}>
          Starts the development server. By default, it auto-detects ports from <code className="text-aquilia-500 font-mono">workspace.py</code>, enabling hot reloading.
        </p>
        <CodeBlock language="bash" filename="Terminal" highlightLines={[2, 5]}>{`# Start server on local defaults
aq run

# Bind custom host/port and disable pre-flight checks
aq run --port=8080 --host=0.0.0.0 --skip-checks`}</CodeBlock>

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
                ['--mode', 'Runs in dev mode (default) or test mode (swaps to test environment database and config).'],
                ['--port', 'Custom port to run on.'],
                ['--host', 'Custom network host to bind to.'],
                ['--reload / --no-reload', 'Enable or disable watchfiles hot-reloading.'],
                ['--skip-checks', 'Skips validation pre-checks to accelerate start times.']
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

      {/* aq serve */}
      <section id="serve" className={sectionClass}>
        <h2 className={h2Class}><DocTerm id="cli.serve">aq serve</DocTerm></h2>
        <p className={pClass}>
          Starts the production ASGI server. Recommended to wrap in Gunicorn using Uvicorn worker threads to manage concurrency.
        </p>
        <CodeBlock language="bash" filename="Terminal" highlightLines={[2, 5]}>{`# Simple serve
aq serve

# Production gunicorn setup with 4 workers and custom bindings
aq serve --use-gunicorn --workers=4 --bind=127.0.0.1:9000 --timeout=60`}</CodeBlock>
      </section>

      {/* aq manifest update */}
      <section id="manifest-update" className={sectionClass}>
        <h2 className={h2Class}><DocTerm id="cli.manifest_update">aq manifest update</DocTerm></h2>
        <p className={pClass}>
          Synchronizes a module manifest by searching the folder structure for untracked controller classes or model definitions.
        </p>
        <CodeBlock language="bash" filename="Terminal" highlightLines={[2, 5]}>{`# Sync payments module manifest
aq manifest update payments

# Perform dry-run sync check (useful in CI scripts)
aq manifest update orders --check`}</CodeBlock>
      </section>

      {/* aq doctor */}
      <section id="doctor" className={sectionClass}>
        <h2 className={h2Class}>aq doctor</h2>
        <p className={pClass}>
          Performs deep diagnostics on your active workspace setup. It validates imports, database adapters, cache connections, and environment files, reporting details in clean stdout or JSON format.
        </p>
        <CodeBlock language="bash" filename="Terminal" highlightLines={[2, 5]}>{`# Run diagnostic check
aq doctor

# Export diagnostic logs as JSON
aq doctor --json`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
