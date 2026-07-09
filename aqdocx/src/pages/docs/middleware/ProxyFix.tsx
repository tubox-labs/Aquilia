import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, Layers } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function MiddlewareProxyFix() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <Layers className="w-4 h-4" />
          <span>MIDDLEWARE / PROXY HEADERS CORRECTION</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          ProxyFixMiddleware
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">ProxyFixMiddleware</code> corrects request schemes, client IPs, and ports when running behind reverse proxies (like Nginx, HAProxy, AWS ALB, or Cloudflare). It uses CIDR networks to restrict header trust to verified proxy IPs.
        </p>
      </div>

      {/* Constructor Parameters */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Constructor Configuration</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Configure header trust boundaries to prevent headers spoofing by malicious clients:
        </p>

        <div className="space-y-4 mb-8 text-sm text-gray-400 font-sans">
          <div className="border-b border-white/5 pb-2">
            <code className="text-white text-xs font-mono">trusted_proxies: list[str] | None = None</code> — CIDR subnet masks or exact IP addresses of trusted proxies. (Defaults to localhost subnets, private subnets <code className="text-aquilia-300">10.0.0.0/8</code>, <code className="text-aquilia-300">172.16.0.0/12</code>, <code className="text-aquilia-300">192.168.0.0/16</code>).
          </div>
          <div className="border-b border-white/5 pb-2">
            <code className="text-white text-xs font-mono">x_for: int = 1</code> — Number of proxy hops to trust/unwrap from the right of <code className="text-white">X-Forwarded-For</code> list.
          </div>
          <div className="border-b border-white/5 pb-2">
            <code className="text-white text-xs font-mono">x_proto: int = 1</code> — Trusted hops for <code className="text-white">X-Forwarded-Proto</code> scheme header.
          </div>
          <div className="border-b border-white/5 pb-2">
            <code className="text-white text-xs font-mono">x_host: int = 1</code> — Trusted hops for <code className="text-white">X-Forwarded-Host</code> domain name header.
          </div>
          <div className="pb-2">
            <code className="text-white text-xs font-mono">x_port: int = 0</code> — Trusted hops for <code className="text-white">X-Forwarded-Port</code> header. (Disabled by default).
          </div>
        </div>
      </section>

      {/* Usage Example */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Usage Example</h2>
        <CodeBlock language="python" filename="proxy_fix_setup.py" highlightLines={[6, 9]}>{`from aquilia.middleware_ext import ProxyFixMiddleware
from aquilia.workspace import Workspace
from aquilia.integrations import MiddlewareChain

workspace = Workspace("myapp").middleware(
    MiddlewareChain().use(
        "aquilia.middleware_ext.security:ProxyFixMiddleware",
        priority=3,
        trusted_proxies=["10.0.0.0/16", "192.168.1.1"],
        x_for=2,                     # Trust dual proxies hops
        x_proto=1
    )
)`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/middleware/overview" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Overview
        </Link>
        <span />
      </div>

      <NextSteps />
    </div>
  )
}
