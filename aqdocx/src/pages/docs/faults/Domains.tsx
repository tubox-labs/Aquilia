import { useTheme } from '../../../context/ThemeContext'
import { AlertTriangle, ArrowLeft, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'


export function FaultsDomains() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <AlertTriangle className="w-4 h-4" />
          <span>FAULTS / FAULT DOMAINS</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Fault Domains
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Fault Domains group errors by their originating subsystem. Each domain has default settings for severity and retries, making it easier to define handling rules across entire subsystems.
        </p>
      </div>

      {/* Domain Defaults Table */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Built-in Subsystem Domains</h2>
        <div className="w-full overflow-x-auto font-sans">
          <table className="w-full text-sm text-left border-collapse">
            <thead>
              <tr className="border-b border-white/10 text-aquilia-400 font-mono text-xs uppercase tracking-wider">
                <th className="py-3 px-4">Fault Domain</th>
                <th className="py-3 px-4">Default Severity</th>
                <th className="py-3 px-4">Default Retryable</th>
                <th className="py-3 px-4">Subsystem Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 text-gray-400 text-xs font-mono">
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3 px-4 text-aquilia-300">FaultDomain.CONFIG</td>
                <td className="py-3 px-4 text-red-400 font-bold">Severity.FATAL</td>
                <td className="py-3 px-4 text-red-500">False</td>
                <td className="py-3 px-4 font-sans">Workspace or application configuration loading errors</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3 px-4 text-aquilia-300">FaultDomain.REGISTRY</td>
                <td className="py-3 px-4 text-red-400 font-bold">Severity.FATAL</td>
                <td className="py-3 px-4 text-red-500">False</td>
                <td className="py-3 px-4 font-sans">AppManifest loading or dependency cycle validation errors</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3 px-4 text-aquilia-300">FaultDomain.DI</td>
                <td className="py-3 px-4 text-orange-400 font-bold">Severity.ERROR</td>
                <td className="py-3 px-4 text-red-500">False</td>
                <td className="py-3 px-4 font-sans">Dependency injection dependency resolution errors</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3 px-4 text-aquilia-300">FaultDomain.ROUTING</td>
                <td className="py-3 px-4 text-orange-400 font-bold">Severity.ERROR</td>
                <td className="py-3 px-4 text-red-500">False</td>
                <td className="py-3 px-4 font-sans">URL matching and compiled routing layout conflicts</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3 px-4 text-aquilia-300">FaultDomain.FLOW</td>
                <td className="py-3 px-4 text-orange-400 font-bold">Severity.ERROR</td>
                <td className="py-3 px-4 text-red-500">False</td>
                <td className="py-3 px-4 font-sans">Pipeline execution flow and context errors</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3 px-4 text-aquilia-300">FaultDomain.EFFECT</td>
                <td className="py-3 px-4 text-orange-400 font-bold">Severity.ERROR</td>
                <td className="py-3 px-4 text-green-500">True</td>
                <td className="py-3 px-4 font-sans">Effect acquisition or provider release exceptions</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3 px-4 text-aquilia-300">FaultDomain.IO</td>
                <td className="py-3 px-4 text-yellow-400 font-bold">Severity.WARN</td>
                <td className="py-3 px-4 text-green-500">True</td>
                <td className="py-3 px-4 font-sans">Local I/O, file reading, or network stream interrupts</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3 px-4 text-aquilia-300">FaultDomain.SECURITY</td>
                <td className="py-3 px-4 text-orange-400 font-bold">Severity.ERROR</td>
                <td className="py-3 px-4 text-red-500">False</td>
                <td className="py-3 px-4 font-sans">Auth guards, CSRF token validation, or CORS blocks</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3 px-4 text-aquilia-300">FaultDomain.SYSTEM</td>
                <td className="py-3 px-4 text-red-400 font-bold">Severity.FATAL</td>
                <td className="py-3 px-4 text-red-500">False</td>
                <td className="py-3 px-4 font-sans">Critical process constraints or machine environment errors</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3 px-4 text-aquilia-300">FaultDomain.MODEL</td>
                <td className="py-3 px-4 text-orange-400 font-bold">Severity.ERROR</td>
                <td className="py-3 px-4 text-red-500">False</td>
                <td className="py-3 px-4 font-sans">ORM Model schema matching and database queries</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3 px-4 text-aquilia-300">FaultDomain.CACHE</td>
                <td className="py-3 px-4 text-orange-400 font-bold">Severity.ERROR</td>
                <td className="py-3 px-4 text-green-500">True</td>
                <td className="py-3 px-4 font-sans">Cache namespace read/write or backend client timeouts</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3 px-4 text-aquilia-300">FaultDomain.STORAGE</td>
                <td className="py-3 px-4 text-orange-400 font-bold">Severity.ERROR</td>
                <td className="py-3 px-4 text-red-500">False</td>
                <td className="py-3 px-4 font-sans">Object storage bucket sync or driver exceptions</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3 px-4 text-aquilia-300">FaultDomain.TASKS</td>
                <td className="py-3 px-4 text-orange-400 font-bold">Severity.ERROR</td>
                <td className="py-3 px-4 text-green-500">True</td>
                <td className="py-3 px-4 font-sans">Background task engine worker thread failures</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3 px-4 text-aquilia-300">FaultDomain.TEMPLATE</td>
                <td className="py-3 px-4 text-orange-400 font-bold">Severity.ERROR</td>
                <td className="py-3 px-4 text-red-500">False</td>
                <td className="py-3 px-4 font-sans">HTML template compile or sandboxed rendering context errors</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3 px-4 text-aquilia-300">FaultDomain.HTTP</td>
                <td className="py-3 px-4 text-yellow-400 font-bold">Severity.WARN</td>
                <td className="py-3 px-4 text-red-500">False</td>
                <td className="py-3 px-4 font-sans">Outbound client HTTP request failures</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/faults/handlers" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Fault Handlers
        </Link>
        <Link to="/docs/faults/advanced" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          Advanced Handlers <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}