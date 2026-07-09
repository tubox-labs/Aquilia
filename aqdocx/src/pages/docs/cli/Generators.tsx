import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { NextSteps } from '../../../components/NextSteps'
import { FileCode, Settings } from 'lucide-react'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function CLIGenerators() {
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
          <FileCode className="w-4 h-4" />
          CLI / Generators
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Code Scaffolding &amp; Generators
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Scaffolding utilities automatically structure workspaces, create new isolation modules, and wire up controllers from templates, reducing boilerplate code.
        </p>
      </div>

      {/* aq init workspace */}
      <section id="init-workspace" className={sectionClass}>
        <h2 className={h2Class}><Settings className="w-5 h-5 text-aquilia-400" /> Workspace Generator</h2>
        <p className={pClass}>
          The <DocTerm id="cli.init_workspace">aq init workspace</DocTerm> command bootstraps a standardized project layout. It generates configurations, helper scripts, and base files:
        </p>
        <CodeBlock language="bash" filename="Terminal">aq init workspace my_project --template=api</CodeBlock>
        
        <h3 className={h3Class}>Scaffold Output Structure</h3>
        <div className={`p-4 font-mono text-xs rounded-xl ${isDark ? 'bg-zinc-900/50 text-gray-300' : 'bg-gray-50 text-gray-700'} mb-6`}>
          {`my_project/
├── workspace.py           # Central workspace definition & configuration
├── starter.py             # Landing controller welcome handler
├── requirements.txt       # Project python dependencies
├── pyproject.toml         # Packaging metadata
├── modules/               # Composable modules folder
└── artifacts/             # Compiled route & DI schema bundles`}
        </div>
      </section>

      {/* aq add module */}
      <section id="add-module" className={sectionClass}>
        <h2 className={h2Class}><Settings className="w-5 h-5 text-aquilia-400" /> Module Scaffolding</h2>
        <p className={pClass}>
          The <DocTerm id="cli.add_module">aq add module</DocTerm> command creates self-contained directories under <code className="text-aquilia-500 font-mono">modules/</code>, appending the module configuration details automatically:
        </p>
        <CodeBlock language="bash" filename="Terminal">aq add module billing --depends-on=users --route-prefix=/v1/billing</CodeBlock>

        <h3 className={h3Class}>Scaffold Output Structure</h3>
        <div className={`p-4 font-mono text-xs rounded-xl ${isDark ? 'bg-zinc-900/50 text-gray-300' : 'bg-gray-50 text-gray-700'} mb-6`}>
          {`modules/billing/
├── __init__.py
├── manifest.py           # Module service & controller registry manifest
├── controllers.py        # Controller implementations
├── models.py             # Database ORM models
├── schemas.py            # Input validation blueprints
├── services.py           # Business service providers
└── tests/                # Module test suites`}
        </div>
      </section>

      {/* aq generate controller */}
      <section id="generate-controller" className={sectionClass}>
        <h2 className={h2Class}><FileCode className="w-5 h-5 text-aquilia-400" /> Controller Generator</h2>
        <p className={pClass}>
          The <DocTerm id="cli.generate_controller">aq generate controller</DocTerm> command scaffolds new controller class files containing routing endpoint templates, status code returns, and lifecycle hooks:
        </p>
        <CodeBlock language="bash" filename="Terminal">{`# Scaffolds CRUD endpoints for User resource
aq generate controller Users --resource=User --with-lifecycle

# Scaffolds simple controller
aq generate controller Health --simple`}</CodeBlock>

        <h3 className={h3Class}>Scaffolding Options</h3>
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
                ['--prefix', 'Explicit route prefix (defaults to /[name]).'],
                ['--resource', 'Resource model name used to scaffold REST CRUD routes.'],
                ['--simple', 'Generate a simple hello world endpoint without extra methods.'],
                ['--with-lifecycle', 'Scaffolds on_startup, on_request, and on_response hook methods.'],
                ['--test', 'Generates a demo controller containing example route guards and validation schemas.'],
                ['--output', 'Path destination for the generated controller file (defaults to controllers/).']
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

      <NextSteps />
    </div>
  )
}