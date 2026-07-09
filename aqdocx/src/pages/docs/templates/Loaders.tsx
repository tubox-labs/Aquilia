import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Layers } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function TemplatesLoaders() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const textMuted = isDark ? 'text-gray-400' : 'text-gray-600'
  const borderMuted = isDark ? 'border-white/5' : 'border-gray-100'

  return (
    <div className="max-w-4xl mx-auto px-4 py-2">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Layers className="w-4 h-4" />
          Templates / Loaders
        </div>
        <h1 className={`text-4xl font-extrabold tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="gradient-text font-mono">Template Loaders & Namespaces</span>
        </h1>
        <p className={`text-lg leading-relaxed ${textMuted}`}>
          Loaders manage how template source strings are located and read. The <DocTerm id="templates.TemplateLoader">TemplateLoader</DocTerm> class resolves template files across multiple project search paths and modules.
        </p>
      </div>

      {/* Namespace Resolution */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Namespace Resolution Formats
        </h2>
        <p className={`text-sm mb-6 ${textMuted}`}>
          The loader determines the physical path of a template based on the naming syntax used inside controller calls or template directives:
        </p>
        <div className="space-y-6">
          {[
            {
              format: 'Relative Paths ("profile.html")',
              desc: 'Resolved within the default module or relative to configured root search paths. Perfect for local template assets.'
            },
            {
              format: 'Module-Namespaced ("users/profile.html")',
              desc: 'Maps directly to modules/users/templates/profile.html. Simplifies module boundaries.'
            },
            {
              format: 'Cross-Module Reference ("@auth/login.html")',
              desc: 'Using the @ prefix targets specific modules directly, resolving to modules/auth/templates/login.html.'
            },
            {
              format: 'Fully-Qualified ("users:profile.html")',
              desc: 'Identical to module-namespaced, resolving users:profile.html to modules/users/templates/profile.html.'
            }
          ].map((item, i) => (
            <div key={i} className="pl-4 border-l-2 border-aquilia-500/20">
              <h4 className={`text-sm font-semibold mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>{item.format}</h4>
              <p className={`text-xs ${textMuted}`}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* TemplateLoader Constructor */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          TemplateLoader Configuration
        </h2>
        <p className={`text-sm mb-6 ${textMuted}`}>
          Instantiate <DocTerm id="templates.TemplateLoader">TemplateLoader</DocTerm> with custom search paths and package mappings:
        </p>
        <CodeBlock
          language="python"
          filename="custom_loader.py"
          highlightLines={[3, 4, 5]}
        >{`from aquilia.templates import TemplateLoader

loader = TemplateLoader(
    search_paths=["templates", "shared_templates"],
    package_loaders={"admin": "aquilia_admin"},
    default_module="home"
)`}</CodeBlock>
      </section>

      {/* Manifest-Aware Auto-Discovery */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Manifest-Aware Loaders
        </h2>
        <p className={`text-sm mb-6 ${textMuted}`}>
          The system can auto-discover template folders by scanning project manifests (`module.aq` or `manifest.py`). Enable this using built-in discovery functions:
        </p>
        <CodeBlock
          language="python"
          filename="discover_templates.py"
          highlightLines={[5, 8]}
        >{`from aquilia.templates.manifest_integration import (
    discover_template_directories, create_manifest_aware_loader
)

# 1. Discover all "templates" directories relative to current path
discovered_dirs = discover_template_directories(scan_manifests=True)

# 2. Generate a ready-to-use loader targeting all discovered paths
manifest_loader = create_manifest_aware_loader(scan_manifests=True)`}</CodeBlock>
      </section>

      {/* TemplateManager */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          TemplateManager
        </h2>
        <p className={`text-sm mb-6 ${textMuted}`}>
          The <DocTerm id="templates.TemplateSandbox">TemplateManager</DocTerm> compiles template source code into bytecode files and runs automated linter audits to catch bugs prior to deployment:
        </p>
        <CodeBlock
          language="python"
          filename="manager_ops.py"
          highlightLines={[6, 9, 13]}
        >{`from aquilia.templates import TemplateManager

manager = TemplateManager(engine=engine, loader=loader)

# 1. Compile all templates to a .surp bytecode archive (Atomic write with HMAC signature)
await manager.compile_all(output_path="artifacts/templates.surp")

# 2. Run template linter (identifies syntax errors, undefined variables, disallowed filters)
issues = await manager.lint_all(strict_undefined=True)
for issue in issues:
    print(issue) # Output format: template.html:line:col: severity: msg [code]

# 3. Retrieve a list of all template paths discovered by loader
available_templates = loader.list_templates()`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${borderMuted}`}>
        <Link to="/docs/templates/engine" className={`flex items-center gap-2 text-sm ${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`}>
          <ArrowLeft className="w-4 h-4" /> TemplateEngine
        </Link>
        <Link to="/docs/templates/security" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400">
          Security <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps
        items={[
          { text: 'Sandboxed Security Policy', link: '/docs/templates/security' },
          { text: 'Mail Subsystem', link: '/docs/mail' },
          { text: 'Developer Integration Guide', link: '/docs/developer-guide' },
        ]}
      />
    </div>
  )
}