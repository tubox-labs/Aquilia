import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Layers, ArrowRight } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { Link } from 'react-router-dom'

interface MiddlewareItem {
  id: string;
  name: string;
  fullName: string;
  priority: number;
  type: 'infra' | 'protocol' | 'security' | 'core';
  description: string;
  isAlwaysOn: boolean;
  codeSnippet: string;
}

const MIDDLEWARE_DATA: MiddlewareItem[] = [
  {
    id: 'exception',
    name: 'Exception Guard',
    fullName: 'aquilia.middleware.ExceptionMiddleware',
    priority: 1,
    type: 'infra',
    description: 'Intercepts uncaught exceptions. Generates styled Atlas debug pages for HTML requests in development, returns sanitised JSON errors in production, and maps standard Python exceptions to corresponding status codes (e.g. PermissionError to 403).',
    isAlwaysOn: false,
    codeSnippet: '# Registration in default fallback chain\nself.middleware_stack.add(\n    ExceptionMiddleware(debug=self._is_debug()),\n    scope="global",\n    priority=1,\n    name="exception"\n)'
  },
  {
    id: 'fault',
    name: 'Fault Interceptor',
    fullName: 'aquilia.faults.engine.FaultMiddleware',
    priority: 2,
    type: 'infra',
    description: 'Framework plumbing layer. Intercepts structured Fault domain signals (e.g. database, auth, validation) thrown by core subsystems and maps them to clean HTTP responses, preventing internal traceback leakage.',
    isAlwaysOn: true,
    codeSnippet: '# Framework infrastructure (always active)\nself.middleware_stack.add(\n    FaultMiddleware(self.fault_engine),\n    scope="global",\n    priority=2,\n    name="faults"\n)'
  },
  {
    id: 'proxyfix',
    name: 'Proxy Fixer',
    fullName: 'aquilia.middleware.ProxyFixMiddleware',
    priority: 3,
    type: 'protocol',
    description: 'Parses upstream proxy headers (e.g. X-Forwarded-For, X-Forwarded-Proto) to correct client IP and request scheme addresses when running behind reverse proxies like Nginx or Cloudflare.',
    isAlwaysOn: false,
    codeSnippet: '# Configure via workspace integration\nworkspace.integrate(\n    Integration.proxy_fix(\n        trusted_proxies=["127.0.0.1"]\n    )\n)'
  },
  {
    id: 'httpsredirect',
    name: 'HTTPS Enforcer',
    fullName: 'aquilia.middleware.HTTPSRedirectMiddleware',
    priority: 4,
    type: 'protocol',
    description: 'Redirects all unencrypted incoming HTTP requests to their secure HTTPS counterparts, enforcing Transport Layer Security (TLS) across all client connections.',
    isAlwaysOn: false,
    codeSnippet: '# Use via fluent chain in workspace.py\nMiddlewareChain().use(\n    "aquilia.middleware.HTTPSRedirectMiddleware",\n    priority=4\n)'
  },
  {
    id: 'requestscope',
    name: 'Request DI Scope',
    fullName: 'aquilia.server.ServerRequestScopeMiddleware',
    priority: 5,
    type: 'infra',
    description: 'Framework plumbing layer. Creates a child request-scoped DI container from the active app module container. Binds request-specific resources (e.g. Session, Identity, RequestCtx) and triggers DI container cleanup on request finalisation.',
    isAlwaysOn: true,
    codeSnippet: '# Framework infrastructure (always active)\nself.middleware_stack.add(\n    ServerRequestScopeMiddleware(self.runtime),\n    scope="global",\n    priority=5,\n    name="request_scope"\n)'
  },
  {
    id: 'versioning',
    name: 'Version Negotiator',
    fullName: 'aquilia.versioning.middleware.VersionMiddleware',
    priority: 5,
    type: 'protocol',
    description: 'Handles API version negotiation based on headers, query strings, or URL prefix strategies. Resolves deprecated or sunset route behavior dynamically.',
    isAlwaysOn: false,
    codeSnippet: '# Enable versioning integration\nworkspace.integrate(\n    Integration.versioning(\n        strategy="header",\n        header_name="X-Api-Version"\n    )\n)'
  },
  {
    id: 'requestid',
    name: 'Request Tracer',
    fullName: 'aquilia.middleware.RequestIdMiddleware',
    priority: 10,
    type: 'infra',
    description: 'Generates or extracts a unique request trace ID (X-Request-ID). Uses fast os.urandom() to generate 16-byte hex strings (~4x faster than uuid.uuid4()) and attaches it to request context and response headers.',
    isAlwaysOn: false,
    codeSnippet: '# Included in .defaults() and .production() presets\nMiddlewareChain.defaults()  # priority: 10'
  },
  {
    id: 'cors',
    name: 'CORS Evaluator',
    fullName: 'aquilia.middleware_ext.security.CORSMiddleware',
    priority: 11,
    type: 'security',
    description: 'Implements Cross-Origin Resource Sharing (CORS). Intercepts OPTIONS preflight requests, validates access origins/methods/credentials, and returns 204 responses immediately to short-circuit the request.',
    isAlwaysOn: false,
    codeSnippet: '# Add to middleware stack in workspace.py\nMiddlewareChain()\n.use(\n    "aquilia.middleware_ext.CORSMiddleware",\n    priority=11,\n    allow_origins=["*"]\n)'
  },
  {
    id: 'ratelimit',
    name: 'Rate Limiter',
    fullName: 'aquilia.middleware_ext.RateLimitMiddleware',
    priority: 12,
    type: 'security',
    description: 'Enforces request frequency limits per IP or client identity using a sliding window algorithm backed by memory or Redis. Short-circuits with a 429 Too Many Requests response on limit breaches.',
    isAlwaysOn: false,
    codeSnippet: '# Add rate limiting with configs\nMiddlewareChain()\n.use(\n    "aquilia.middleware_ext.RateLimitMiddleware",\n    priority=12,\n    default_limit=100,\n    default_window=60.0\n)'
  },
  {
    id: 'session',
    name: 'Session Loader',
    fullName: 'aquilia.sessions.middleware.SessionMiddleware',
    priority: 15,
    type: 'core',
    description: 'Restores cryptographically signed session data from request cookies into context state, and saves updated session state back to the cookie or backend session store on response egress.',
    isAlwaysOn: false,
    codeSnippet: '# Configure session integration\nworkspace.integrate(\n    Integration.session(\n        cookie_name="aq_session",\n        max_age=3600\n    )\n)'
  },
  {
    id: 'auth',
    name: 'Identity Authenticator',
    fullName: 'aquilia.auth.middleware.AquilAuthMiddleware',
    priority: 15,
    type: 'core',
    description: 'Extracts credentials or JWT tokens from request headers/cookies, validates them using active guards (e.g. Session, JWT, OAuth), and populates ctx.identity with the authenticated subject.',
    isAlwaysOn: false,
    codeSnippet: '# Enable auth integration (requires sessions)\nworkspace.integrate(\n    Integration.auth(guard="jwt")\n)'
  },
  {
    id: 'csrf',
    name: 'CSRF Shield',
    fullName: 'aquilia.middleware_ext.CSRFMiddleware',
    priority: 20,
    type: 'security',
    description: 'Protects state-modifying requests (POST, PUT, DELETE, PATCH) by validating double-submit CSRF cookie tokens, blocking unauthorized requests with a 403 Forbidden response.',
    isAlwaysOn: false,
    codeSnippet: '# Enable via security integration\nworkspace.integrate(\n    Integration.security(csrf_enabled=True)\n)'
  },
  {
    id: 'template',
    name: 'Template Contextualizer',
    fullName: 'aquilia.middleware_ext.TemplateMiddleware',
    priority: 25,
    type: 'core',
    description: 'Injects template rendering functions and contextual variables (like active session, CSRF token, and user identity) into the RequestCtx for seamless frontend rendering.',
    isAlwaysOn: false,
    codeSnippet: '# Configure templates integration\nworkspace.integrate(\n    Integration.templates(directory="templates/")\n)'
  },
  {
    id: 'cache',
    name: 'Response Cache',
    fullName: 'aquilia.middleware_ext.CacheMiddleware',
    priority: 26,
    type: 'core',
    description: 'Inspects outgoing response headers for cacheability directives. Caches GET responses in memory or Redis and serves subsequent identical requests immediately, short-circuiting downstream routes.',
    isAlwaysOn: false,
    codeSnippet: '# Configure caching middleware\nMiddlewareChain()\n.use(\n    "aquilia.middleware_ext.CacheMiddleware",\n    priority=26,\n    default_ttl=300\n)'
  }
];

const ARCHITECTURE_DETAILS: Record<string, { title: string; subtitle: string; body: string }> = {
  workspace: {
    title: "Workspace Config Declarations",
    subtitle: "workspace.py / Integration API",
    body: "Middlewares are registered globally using the workspace object, typically inside `workspace.py` or configuration plugins. For instance, `workspace.integrate(Integration.cache(...))` registers caching mechanisms globally. This provides the primary baseline stack configuration."
  },
  manifest: {
    title: "Module AppManifest declarations",
    subtitle: "manifest.py / Module Config",
    body: "Each local application module declares its routes, controllers, and middlewares within its `AppManifest` definition. Middlewares defined here can be scoped with parameters like `priority` and `scope` to control where they fit in the sorted execution stack."
  },
  scanner: {
    title: "Package & Manifest Scanner",
    subtitle: "Discovery & Autoloading",
    body: "During server bootstrap, the autodiscovery engine (using PackageScanner) walks package directories, imports manifest.py files, scans annotations, and aggregates all user-declared middleware descriptors into a central catalog."
  },
  sorting: {
    title: "Stack Sorting Engine",
    subtitle: "MiddlewareStack Priority Sorting",
    body: "The compiler sorts all registered middlewares in ascending order of `(scope_rank, priority)`. Scopes are ranked: Global (0), App (1), Controller (2), and Route (3). This ensures infrastructure components outer-wrap specific route handlers."
  },
  compilation: {
    title: "Closure Nesting Chain",
    subtitle: "build_handler() Wrapping",
    body: "The compiler wraps sorted middlewares in REVERSE order. Each middleware wraps the next as a closure, accepting `next_handler` as a parameter. Thus, the lowest priority (P1 Exception Guard) becomes the outermost boundary layer, running first on request ingress and last on response egress."
  },
  asgi: {
    title: "ASGI Connection Ingress",
    subtitle: "ASGIAdapter / Scope Mapping",
    body: "ASGIAdapter accepts raw ASGI events, parses HTTP headers/WS protocols, and maps them to a pool-allocated RequestCtx. It routes the request and binds it to request-scoped lifecycle hooks."
  },
  di: {
    title: "Request DI Container",
    subtitle: "Scoped Injection resolution",
    body: "Spawns a child Dependency Injection container for the lifetime of this specific request, enabling controller methods and services to resolve request-scoped or module-scoped resources dynamically."
  },
  exception: {
    title: "Exception Guard",
    subtitle: "Priority 1 (Infrastructure)",
    body: "The absolute outermost middleware wrapper. It acts as a safety harness, catching any unhandled exceptions bubbling up from inner layers and translating them into developer debug interfaces or clean JSON responses."
  },
  fault: {
    title: "Fault Interceptor",
    subtitle: "Priority 2 (Infrastructure)",
    body: "An infrastructure gateway that catches Aquilia `Fault` exception signals. It formats and returns structured error payloads for database, auth, or validation faults, halting further routing."
  },
  scope: {
    title: "Request Scope Middleware",
    subtitle: "Priority 5 (Infrastructure)",
    body: "Framework plumbing that manages the request DI lifecycle. It injects the request scope variables and cleans up resources once the response exits the stack."
  },
  auth: {
    title: "Auth & Session Loader",
    subtitle: "Priority 15 (Security / State)",
    body: "Loads sessions from state stores, parses cookies, validates tokens, and assigns the verified identity to `request.state.user`. If credentials fail clearance, it can short-circuit the request here."
  },
  cache: {
    title: "Response Caching",
    subtitle: "Priority 26 (Performance / Core)",
    body: "The innermost default middleware. Checks GET requests against caching backends. If a matching response is cached, it returns it instantly, bypassing controller execution and short-circuiting egress."
  },
  controller: {
    title: "Controller Target Route",
    subtitle: "Core Route Handler Dispatch",
    body: "The core of the execution. The ControllerRouter matches the final path, resolves the controller instance via request DI, applies module guards, filters request blueprints, and triggers the controller method."
  }
};

function MiddlewareArchitectureDiagram({ isDark }: { isDark: boolean }) {
  const [activeTab, setActiveTab] = useState<'build' | 'runtime'>('build');
  const [selectedNode, setSelectedNode] = useState<string>('workspace');

  const handleTabChange = (tab: 'build' | 'runtime') => {
    setActiveTab(tab);
    setSelectedNode(tab === 'build' ? 'workspace' : 'asgi');
  };

  const details = ARCHITECTURE_DETAILS[selectedNode] || ARCHITECTURE_DETAILS.workspace;

  return (
    <div className="w-full my-12 pb-6 border-b border-zinc-850 font-sans">
      {/* Tab Switcher & Title */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <div>
          <h3 className={`text-xs font-mono font-bold tracking-widest uppercase ${isDark ? 'text-zinc-400' : 'text-gray-600'}`}>
            System Architecture & Lifecycle
          </h3>
          <p className={`text-[11px] ${isDark ? 'text-zinc-600' : 'text-gray-400'}`}>
            Select a phase to explore compiling logic and runtime traversal.
          </p>
        </div>

        {/* Tab buttons */}
        <div className="flex items-center gap-6 text-xs font-mono">
          <button
            onClick={() => handleTabChange('build')}
            className={`relative py-1 cursor-pointer transition-colors ${
              activeTab === 'build'
                ? (isDark ? 'text-emerald-400 font-bold' : 'text-emerald-600 font-bold')
                : (isDark ? 'text-zinc-500 hover:text-zinc-300' : 'text-gray-400 hover:text-gray-600')
            }`}
          >
            1. Compilation & Sorting
            {activeTab === 'build' && (
              <motion.div layoutId="archTabUnderline" className="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-500" />
            )}
          </button>
          <button
            onClick={() => handleTabChange('runtime')}
            className={`relative py-1 cursor-pointer transition-colors ${
              activeTab === 'runtime'
                ? (isDark ? 'text-emerald-400 font-bold' : 'text-emerald-600 font-bold')
                : (isDark ? 'text-zinc-500 hover:text-zinc-300' : 'text-gray-400 hover:text-gray-600')
            }`}
          >
            2. Runtime Traversal
            {activeTab === 'runtime' && (
              <motion.div layoutId="archTabUnderline" className="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-500" />
            )}
          </button>
        </div>
      </div>

      <AnimatePresence mode="wait">
        {activeTab === 'build' ? (
          <motion.div
            key="build"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.15 }}
            className="w-full overflow-x-auto"
          >
            <div className="min-w-[760px] flex justify-center py-4">
              <svg viewBox="0 0 800 240" className="w-full max-w-[800px] h-auto bg-transparent select-none">
                <defs>
                  <filter id="glow-emerald" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="3" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                  </filter>
                  <marker id="arrow-gray" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse">
                    <path d="M 0 1 L 10 5 L 0 9 z" fill={isDark ? "#3f3f46" : "#cbd5e1"} />
                  </marker>
                </defs>

                {/* Columns layout connectors */}
                <g opacity="0.1" stroke={isDark ? "#ffffff" : "#000000"} strokeWidth="0.5" strokeDasharray="4,4">
                  <line x1="240" y1="30" x2="240" y2="210" />
                  <line x1="450" y1="30" x2="450" y2="210" />
                </g>

                {/* Stages titles */}
                <text x="135" y="25" textAnchor="middle" fill={isDark ? "#52525b" : "#a1a1aa"} fontSize="8" fontWeight="bold" fontFamily="monospace">CONFIG DECLARATIONS</text>
                <text x="345" y="25" textAnchor="middle" fill={isDark ? "#52525b" : "#a1a1aa"} fontSize="8" fontWeight="bold" fontFamily="monospace">DISCOVERY & AGGREGATION</text>
                <text x="625" y="25" textAnchor="middle" fill={isDark ? "#52525b" : "#a1a1aa"} fontSize="8" fontWeight="bold" fontFamily="monospace">COMPILED STACK</text>

                {/* Flows */}
                {/* workspace -> scanner */}
                <path d="M 190,70 H 215 C 225,70 235,80 245,95 L 265,110" fill="none" stroke={isDark ? "#3f3f46" : "#e4e4e7"} strokeWidth="1.2" strokeDasharray="3,3" />
                {/* manifest -> scanner */}
                <path d="M 190,170 H 215 C 225,170 235,160 245,145 L 265,130" fill="none" stroke={isDark ? "#3f3f46" : "#e4e4e7"} strokeWidth="1.2" strokeDasharray="3,3" />
                {/* scanner -> sorting */}
                <line x1="390" y1="120" x2="465" y2="120" stroke={isDark ? "#52525b" : "#cbd5e1"} strokeWidth="1.5" markerEnd="url(#arrow-gray)" />
                {/* sorting -> compilation */}
                <line x1="590" y1="120" x2="665" y2="120" stroke={isDark ? "#52525b" : "#cbd5e1"} strokeWidth="1.5" markerEnd="url(#arrow-gray)" />

                {/* 1. Workspace integrations node */}
                <g 
                  onClick={() => setSelectedNode('workspace')}
                  className="cursor-pointer"
                  transform="translate(30, 48)"
                >
                  <rect 
                    x="0" y="0" width="160" height="44" rx="8"
                    fill={isDark ? "#09090b" : "#ffffff"} 
                    stroke={selectedNode === 'workspace' ? "#10b981" : (isDark ? "#27272a" : "#e4e4e7")} 
                    strokeWidth={selectedNode === 'workspace' ? "2" : "1"}
                    filter={selectedNode === 'workspace' ? "url(#glow-emerald)" : "none"}
                  />
                  <text x="12" y="18" fill={isDark ? "#e4e4e7" : "#1f2937"} fontSize="9" fontWeight="bold" fontFamily="monospace">workspace.py</text>
                  <text x="12" y="32" fill={isDark ? "#71717a" : "#71717a"} fontSize="8">workspace.integrate()</text>
                  <circle cx="145" cy="22" r="4" fill="#ef4444" />
                </g>

                {/* 2. Manifest modules node */}
                <g 
                  onClick={() => setSelectedNode('manifest')}
                  className="cursor-pointer"
                  transform="translate(30, 148)"
                >
                  <rect 
                    x="0" y="0" width="160" height="44" rx="8"
                    fill={isDark ? "#09090b" : "#ffffff"} 
                    stroke={selectedNode === 'manifest' ? "#10b981" : (isDark ? "#27272a" : "#e4e4e7")} 
                    strokeWidth={selectedNode === 'manifest' ? "2" : "1"}
                    filter={selectedNode === 'manifest' ? "url(#glow-emerald)" : "none"}
                  />
                  <text x="12" y="18" fill={isDark ? "#e4e4e7" : "#1f2937"} fontSize="9" fontWeight="bold" fontFamily="monospace">manifest.py</text>
                  <text x="12" y="32" fill={isDark ? "#71717a" : "#71717a"} fontSize="8">AppManifest(middleware=[...])</text>
                  <circle cx="145" cy="22" r="4" fill="#3b82f6" />
                </g>

                {/* 3. PackageScanner node */}
                <g 
                  onClick={() => setSelectedNode('scanner')}
                  className="cursor-pointer"
                  transform="translate(265, 98)"
                >
                  <rect 
                    x="0" y="0" width="125" height="44" rx="8"
                    fill={isDark ? "#09090b" : "#ffffff"} 
                    stroke={selectedNode === 'scanner' ? "#10b981" : (isDark ? "#27272a" : "#e4e4e7")} 
                    strokeWidth={selectedNode === 'scanner' ? "2" : "1"}
                    filter={selectedNode === 'scanner' ? "url(#glow-emerald)" : "none"}
                  />
                  <text x="12" y="18" fill={isDark ? "#e4e4e7" : "#1f2937"} fontSize="9" fontWeight="bold">PackageScanner</text>
                  <text x="12" y="32" fill={isDark ? "#71717a" : "#71717a"} fontSize="8">Collects descriptors</text>
                </g>

                {/* 4. MiddlewareStack Sorter */}
                <g 
                  onClick={() => setSelectedNode('sorting')}
                  className="cursor-pointer"
                  transform="translate(465, 98)"
                >
                  <rect 
                    x="0" y="0" width="125" height="44" rx="8"
                    fill={isDark ? "#09090b" : "#ffffff"} 
                    stroke={selectedNode === 'sorting' ? "#10b981" : (isDark ? "#27272a" : "#e4e4e7")} 
                    strokeWidth={selectedNode === 'sorting' ? "2" : "1"}
                    filter={selectedNode === 'sorting' ? "url(#glow-emerald)" : "none"}
                  />
                  <text x="12" y="18" fill={isDark ? "#e4e4e7" : "#1f2937"} fontSize="9" fontWeight="bold">MiddlewareStack</text>
                  <text x="12" y="32" fill={isDark ? "#10b981" : "#059669"} fontSize="8" fontWeight="bold" fontFamily="monospace">Sort: scope + priority</text>
                </g>

                {/* 5. Compilation chain output */}
                <g 
                  onClick={() => setSelectedNode('compilation')}
                  className="cursor-pointer"
                  transform="translate(665, 98)"
                >
                  <rect 
                    x="0" y="0" width="105" height="44" rx="8"
                    fill={isDark ? "#064e3b" : "#d1fae5"} 
                    stroke={selectedNode === 'compilation' ? "#10b981" : (isDark ? "#047857" : "#a7f3d0")} 
                    strokeWidth={selectedNode === 'compilation' ? "2" : "1"}
                    filter={selectedNode === 'compilation' ? "url(#glow-emerald)" : "none"}
                  />
                  <text x="12" y="18" fill={isDark ? "#34d399" : "#065f46"} fontSize="9" fontWeight="bold" fontFamily="monospace">build_handler()</text>
                  <text x="12" y="32" fill={isDark ? "#a7f3d0" : "#047857"} fontSize="8">Nested Callables</text>
                </g>
              </svg>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="runtime"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.15 }}
            className="w-full overflow-x-auto"
          >
            <div className="min-w-[760px] flex justify-center py-4">
              <svg viewBox="0 0 800 260" className="w-full max-w-[800px] h-auto bg-transparent select-none">
                <defs>
                  <filter id="glow-blue" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="3" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                  </filter>
                  <marker id="arrow-green" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse">
                    <path d="M 0 1 L 10 5 L 0 9 z" fill="#10b981" />
                  </marker>
                  <marker id="arrow-blue" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse">
                    <path d="M 0 1 L 10 5 L 0 9 z" fill="#3b82f6" />
                  </marker>
                  <marker id="arrow-red" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse">
                    <path d="M 0 1 L 10 5 L 0 9 z" fill="#ef4444" />
                  </marker>
                </defs>

                {/* Ingress boundaries */}
                <g opacity="0.08" stroke={isDark ? "#ffffff" : "#000000"} strokeWidth="0.5" strokeDasharray="4,4">
                  <line x1="170" y1="20" x2="170" y2="240" />
                  <line x1="600" y1="20" x2="600" y2="240" />
                </g>

                {/* Section labels */}
                <text x="95" y="20" textAnchor="middle" fill={isDark ? "#52525b" : "#a1a1aa"} fontSize="8" fontWeight="bold" fontFamily="monospace">INGRESS</text>
                <text x="385" y="20" textAnchor="middle" fill={isDark ? "#52525b" : "#a1a1aa"} fontSize="8" fontWeight="bold" fontFamily="monospace">TRAVERSAL PIPELINE</text>
                <text x="700" y="20" textAnchor="middle" fill={isDark ? "#52525b" : "#a1a1aa"} fontSize="8" fontWeight="bold" fontFamily="monospace">CONTROLLER CORE</text>

                {/* Top Request Path (Green, Left-to-Right) */}
                <path d="M 30,75 H 120 C 130,75 140,75 150,75 H 560 C 570,75 580,85 590,105 L 610,145" 
                      fill="none" stroke="#10b981" strokeWidth="1.5" markerEnd="url(#arrow-green)" />
                
                {/* Bottom Response Path (Blue, Right-to-Left) */}
                <path d="M 610,145 L 590,185 C 580,205 570,215 560,215 H 150 H 120 C 110,215 100,215 90,215 H 30"
                      fill="none" stroke="#3b82f6" strokeWidth="1.5" markerEnd="url(#arrow-blue)" />

                {/* Flow dots */}
                <motion.circle r="3" fill="#10b981"
                  animate={{ cx: [30, 120, 560, 610], cy: [75, 75, 75, 145] }}
                  transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
                />
                <motion.circle r="3" fill="#3b82f6"
                  animate={{ cx: [610, 560, 120, 30], cy: [145, 215, 215, 215] }}
                  transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
                />

                {/* ASGI Adapter node */}
                <g 
                  onClick={() => setSelectedNode('asgi')}
                  className="cursor-pointer"
                  transform="translate(90, 50)"
                >
                  <circle 
                    cx="20" cy="25" r="16" 
                    fill={isDark ? "#09090b" : "#ffffff"} 
                    stroke={selectedNode === 'asgi' ? "#10b981" : (isDark ? "#27272a" : "#e4e4e7")}
                    strokeWidth={selectedNode === 'asgi' ? "2" : "1"}
                  />
                  <text x="20" y="28" textAnchor="middle" fill={isDark ? "#e4e4e7" : "#1f2937"} fontSize="8" fontWeight="bold" fontFamily="monospace">ASGI</text>
                  <text x="20" y="52" textAnchor="middle" fill={isDark ? "#71717a" : "#71717a"} fontSize="7">ASGIAdapter</text>
                </g>

                {/* Scoped DI Container setup */}
                <g 
                  onClick={() => setSelectedNode('di')}
                  className="cursor-pointer"
                  transform="translate(90, 190)"
                >
                  <circle 
                    cx="20" cy="25" r="16" 
                    fill={isDark ? "#09090b" : "#ffffff"} 
                    stroke={selectedNode === 'di' ? "#3b82f6" : (isDark ? "#27272a" : "#e4e4e7")}
                    strokeWidth={selectedNode === 'di' ? "2" : "1"}
                  />
                  <text x="20" y="28" textAnchor="middle" fill={isDark ? "#e4e4e7" : "#1f2937"} fontSize="8" fontWeight="bold" fontFamily="monospace">DI</text>
                  <text x="20" y="52" textAnchor="middle" fill={isDark ? "#71717a" : "#71717a"} fontSize="7">Request Scope</text>
                </g>

                {/* Staggered Gateway Nodes */}
                {[
                  { id: 'exception', x: 210, name: "Exception", prio: "P1", isTop: true },
                  { id: 'fault', x: 290, name: "Fault", prio: "P2", isTop: false },
                  { id: 'scope', x: 370, name: "RequestScope", prio: "P5", isTop: true },
                  { id: 'auth', x: 450, name: "Auth/Session", prio: "P15", isTop: false },
                  { id: 'cache', x: 530, name: "Response Cache", prio: "P26", isTop: true }
                ].map((node) => {
                  const isSelected = selectedNode === node.id;
                  const circleY = 145;
                  const labelY = node.isTop ? 108 : 192;

                  return (
                    <g key={node.id} className="cursor-pointer" onClick={() => setSelectedNode(node.id)}>
                      {/* Vertical wrap line */}
                      <line x1={node.x} y1="75" x2={node.x} y2="215" stroke={isDark ? "#27272a" : "#e4e4e7"} strokeWidth="1" strokeDasharray="3,3" />
                      
                      {/* Circle node */}
                      <circle 
                        cx={node.x} cy={circleY} r="9" 
                        fill={isDark ? "#09090b" : "#ffffff"} 
                        stroke={isSelected ? "#10b981" : (isDark ? "#3f3f46" : "#cbd5e1")} 
                        strokeWidth={isSelected ? "2" : "1.2"} 
                      />
                      <text x={node.x} y={circleY + 3} textAnchor="middle" fill={isDark ? "#71717a" : "#71717a"} fontSize="7" fontFamily="monospace" fontWeight="bold">{node.prio}</text>

                      {/* Staggered text label to prevent horizontal collisions */}
                      <text 
                        x={node.x} y={labelY} textAnchor="middle" 
                        fill={isSelected ? (isDark ? "#ffffff" : "#000000") : (isDark ? "#a1a1aa" : "#71717a")} 
                        fontSize="8.5" fontWeight={isSelected ? "bold" : "normal"}
                      >
                        {node.name}
                      </text>

                      {/* Direction indicators */}
                      <path d={`M ${node.x - 5},90 L ${node.x},95 L ${node.x + 5},90`} fill="none" stroke="#10b981" strokeWidth="1" opacity="0.6" />
                      <path d={`M ${node.x - 5},200 L ${node.x},195 L ${node.x + 5},200`} fill="none" stroke="#3b82f6" strokeWidth="1" opacity="0.6" />
                    </g>
                  );
                })}

                {/* Short-Circuit Path (Red dashed line from Auth) */}
                <path d="M 450,75 V 110 C 450,175 480,215 450,215" fill="none" stroke="#ef4444" strokeWidth="1.2" strokeDasharray="4,2" markerEnd="url(#arrow-red)" />

                {/* Controller target node */}
                <g 
                  onClick={() => setSelectedNode('controller')}
                  className="cursor-pointer"
                  transform="translate(610, 115)"
                >
                  <rect 
                    x="10" y="10" width="80" height="40" rx="8"
                    fill={isDark ? "#064e3b" : "#d1fae5"} 
                    stroke={selectedNode === 'controller' ? "#10b981" : (isDark ? "#047857" : "#a7f3d0")} 
                    strokeWidth={selectedNode === 'controller' ? "2" : "1"}
                  />
                  <text x="50" y="28" textAnchor="middle" fill={isDark ? "#34d399" : "#065f46"} fontSize="9.5" fontWeight="bold" fontFamily="monospace">CORE</text>
                  <text x="50" y="42" textAnchor="middle" fill={isDark ? "#a7f3d0" : "#047857"} fontSize="7" uppercase="true">Controller</text>
                </g>
              </svg>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Typographic details block (No boxes!) */}
      <div className="mt-4 pt-6 border-t border-dashed border-zinc-850">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 mb-2">
          <span className={`text-[10px] font-mono tracking-wider font-bold ${isDark ? 'text-emerald-400' : 'text-emerald-600'}`}>
            {details.subtitle.toUpperCase()}
          </span>
          <span className={`text-[10px] font-mono ${isDark ? 'text-zinc-600' : 'text-gray-400'}`}>
            Target: {selectedNode}
          </span>
        </div>
        <h4 className={`text-md font-mono font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          {details.title}
        </h4>
        <p className={`text-xs leading-relaxed font-light max-w-3xl ${isDark ? 'text-zinc-400' : 'text-gray-600'}`}>
          {details.body}
        </p>
      </div>
    </div>
  );
}

function MiddlewarePipelineVisualizer({ isDark }: { isDark: boolean }) {
  const [viewMode, setViewMode] = useState<'timeline' | 'onion'>('timeline');
  const [selectedId, setSelectedId] = useState('exception');
  
  const selectedItem = MIDDLEWARE_DATA.find(m => m.id === selectedId) || MIDDLEWARE_DATA[0];
  
  const getCoordinates = (radius: number, angleDegrees: number) => {
    const angleRadians = (angleDegrees - 90) * Math.PI / 180;
    const x = 200 + radius * Math.cos(angleRadians);
    const y = 200 + radius * Math.sin(angleRadians);
    return { x, y };
  };

  const getThemeColor = (type: string) => {
    switch (type) {
      case 'infra': return 'text-red-500 border-red-500/20';
      case 'protocol': return 'text-blue-400 border-blue-400/20';
      case 'security': return 'text-amber-500 border-amber-500/20';
      case 'core': return 'text-emerald-500 border-emerald-500/20';
      default: return 'text-gray-400 border-gray-400/20';
    }
  };

  const getThemeColorHex = (type: string) => {
    switch (type) {
      case 'infra': return '#ef4444';
      case 'protocol': return '#60a5fa';
      case 'security': return '#f59e0b';
      case 'core': return '#10b981';
      default: return '#9ca3af';
    }
  };

  return (
    <div className="my-12 font-sans">
      {/* Top Header & Controls */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8 pb-4 border-b border-zinc-850">
        <div>
          <h3 className={`text-md font-mono font-bold tracking-tight uppercase ${isDark ? 'text-white' : 'text-gray-900'}`}>
            Interactive Pipeline Flow
          </h3>
          <p className={`text-xs ${isDark ? 'text-zinc-500' : 'text-gray-500'}`}>
            Click on any node to expand details and registration API.
          </p>
        </div>
        
        {/* Minimalist Switcher */}
        <div className="flex items-center gap-6 text-xs font-mono">
          <button
            onClick={() => setViewMode('timeline')}
            className={`relative py-1 cursor-pointer transition-colors ${
              viewMode === 'timeline'
                ? (isDark ? 'text-emerald-400 font-bold' : 'text-emerald-600 font-bold')
                : (isDark ? 'text-zinc-500 hover:text-zinc-300' : 'text-gray-400 hover:text-gray-600')
            }`}
          >
            Spine Flow
            {viewMode === 'timeline' && (
              <motion.div layoutId="activeTabUnderline" className="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-500" />
            )}
          </button>
          <button
            onClick={() => setViewMode('onion')}
            className={`relative py-1 cursor-pointer transition-colors ${
              viewMode === 'onion'
                ? (isDark ? 'text-emerald-400 font-bold' : 'text-emerald-600 font-bold')
                : (isDark ? 'text-zinc-500 hover:text-zinc-300' : 'text-gray-400 hover:text-gray-600')
            }`}
          >
            Onion Rings
            {viewMode === 'onion' && (
              <motion.div layoutId="activeTabUnderline" className="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-500" />
            )}
          </button>
        </div>
      </div>

      <AnimatePresence mode="wait">
        {viewMode === 'timeline' ? (
          <motion.div
            key="timeline"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.15 }}
            className="relative pl-6"
          >
            {/* The single vertical timeline spine line */}
            <div className={`absolute left-[5.5px] top-2 bottom-2 w-[1px] ${
              isDark ? 'bg-zinc-800' : 'bg-gray-200'
            }`} />

            <div className="flex flex-col gap-6">
              {MIDDLEWARE_DATA.map((mw) => {
                const isSelected = mw.id === selectedId;
                const themeColorClass = getThemeColor(mw.type);
                const colorHex = getThemeColorHex(mw.type);

                return (
                  <div key={mw.id} className="relative flex flex-col items-start group">
                    {/* The timeline dot */}
                    <div
                      onClick={() => setSelectedId(mw.id)}
                      className={`absolute -left-[26px] top-1.5 w-3 h-3 rounded-full border-2 cursor-pointer transition-all z-10 ${
                        isSelected 
                          ? 'scale-125' 
                          : 'opacity-60 group-hover:opacity-100'
                      }`}
                      style={{
                        borderColor: colorHex,
                        backgroundColor: isSelected ? colorHex : (isDark ? '#000000' : '#ffffff'),
                        boxShadow: isSelected ? `0 0 8px ${colorHex}` : 'none'
                      }}
                    />

                    {/* Node Header Row */}
                    <div 
                      onClick={() => setSelectedId(mw.id)}
                      className="flex items-center gap-3 cursor-pointer select-none"
                    >
                      <span className={`text-[10px] font-mono font-bold tracking-wider ${themeColorClass}`}>
                        P{mw.priority.toString().padStart(2, '0')}
                      </span>
                      <span className={`text-sm font-mono font-bold transition-colors ${
                        isSelected
                          ? (isDark ? 'text-white' : 'text-gray-900')
                          : (isDark ? 'text-zinc-500 hover:text-zinc-300' : 'text-gray-400 hover:text-gray-600')
                      }`}>
                        {mw.name}
                      </span>
                      {mw.isAlwaysOn && (
                        <span className={`text-[8px] font-mono tracking-widest uppercase opacity-40 ${isDark ? 'text-zinc-400' : 'text-gray-600'}`}>
                          • Always On
                        </span>
                      )}
                    </div>

                    {/* Accordion Content */}
                    <AnimatePresence initial={false}>
                      {isSelected && (
                        <motion.div
                          initial={{ height: 0, opacity: 0, marginTop: 0 }}
                          animate={{ height: 'auto', opacity: 1, marginTop: 8 }}
                          exit={{ height: 0, opacity: 0, marginTop: 0 }}
                          transition={{ duration: 0.2 }}
                          className="overflow-hidden w-full max-w-2xl"
                        >
                          <div className={`text-xs pl-0 pr-4 pb-2 space-y-4 ${isDark ? 'text-zinc-400 font-light' : 'text-gray-600 font-normal'}`}>
                            <p className="leading-relaxed">{mw.description}</p>
                            
                            <div className="flex flex-col gap-1 font-mono text-[10px]">
                              <span className={isDark ? 'text-zinc-500' : 'text-gray-400'}>IMPORT PATH</span>
                              <span className={`break-all ${isDark ? 'text-zinc-300' : 'text-gray-800'}`}>
                                {mw.fullName}
                              </span>
                            </div>

                            <div className="space-y-1">
                              <span className={`font-mono text-[10px] block ${isDark ? 'text-zinc-500' : 'text-gray-400'}`}>REGISTRATION API</span>
                              <div className="font-mono text-[9px] rounded-lg overflow-hidden bg-black/40 border border-zinc-800/40">
                                <CodeBlock language="python" filename="" showLineNumbers={false}>
                                  {mw.codeSnippet}
                                </CodeBlock>
                              </div>
                            </div>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                );
              })}
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="onion"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.15 }}
            className="flex flex-col items-center gap-8 w-full"
          >
            {/* Concentric rings SVG container */}
            <div className="relative w-full max-w-[340px] aspect-square">
              <svg viewBox="0 0 400 400" className="w-full h-full bg-transparent">
                {/* Concentric rings */}
                <circle cx="200" cy="200" r="180" fill="none" stroke={isDark ? "#27272a" : "#e4e4e7"} strokeWidth="1" strokeDasharray="3,3" />
                <circle cx="200" cy="200" r="135" fill="none" stroke={isDark ? "#27272a" : "#e4e4e7"} strokeWidth="1" strokeDasharray="3,3" />
                <circle cx="200" cy="200" r="90" fill="none" stroke={isDark ? "#27272a" : "#e4e4e7"} strokeWidth="1" strokeDasharray="3,3" />
                <circle cx="200" cy="200" r="45" fill="none" stroke={isDark ? "#27272a" : "#e4e4e7"} strokeWidth="1" strokeDasharray="3,3" />

                {/* Core (Controller) */}
                <circle cx="200" cy="200" r="24" fill={isDark ? "#064e3b" : "#d1fae5"} stroke="#10b981" strokeWidth="2" className="animate-pulse" />
                <text x="200" y="203" textAnchor="middle" fill="#10b981" fontSize="7" fontWeight="bold" fontFamily="monospace">CORE</text>

                {/* Render nodes */}
                {MIDDLEWARE_DATA.map((mw) => {
                  let radius = 180;
                  let angle = 45;
                  if (mw.type === 'infra') { radius = 180; }
                  else if (mw.type === 'protocol') { radius = 135; }
                  else if (mw.type === 'security') { radius = 90; }
                  else if (mw.type === 'core') { radius = 45; }

                  const nodesOfSameType = MIDDLEWARE_DATA.filter(m => m.type === mw.type);
                  const idx = nodesOfSameType.findIndex(m => m.id === mw.id);
                  const count = nodesOfSameType.length;

                  angle = (idx * (360 / count)) + (mw.type === 'protocol' ? 30 : 0);

                  const { x, y } = getCoordinates(radius, angle);
                  const isSelected = mw.id === selectedId;
                  const colorHex = getThemeColorHex(mw.type);

                  return (
                    <g key={mw.id} className="cursor-pointer" onClick={() => setSelectedId(mw.id)}>
                      {isSelected && (
                        <circle cx={x} cy={y} r="12" fill="none" stroke={colorHex} strokeWidth="1" opacity="0.6" className="animate-ping" />
                      )}
                      <circle
                        cx={x}
                        cy={y}
                        r={isSelected ? "7" : "5"}
                        fill={isSelected ? colorHex : (isDark ? "#000000" : "#ffffff")}
                        stroke={colorHex}
                        strokeWidth={isSelected ? "2" : "1.5"}
                      />
                      <text
                        x={x}
                        y={y - 10}
                        textAnchor="middle"
                        fill={isSelected ? (isDark ? "#ffffff" : "#000000") : (isDark ? "#a1a1aa" : "#71717a")}
                        fontSize="8"
                        fontWeight={isSelected ? "bold" : "normal"}
                        fontFamily="monospace"
                        className="pointer-events-none"
                      >
                        P{mw.priority}
                      </text>
                    </g>
                  );
                })}
              </svg>
            </div>

            {/* Flat typographic details display (No boxes!) */}
            <div className="w-full max-w-xl">
              <div className="flex justify-between items-center mb-3">
                <span className={`text-[9px] font-mono px-2 py-0.5 rounded border font-semibold ${getThemeColor(selectedItem.type)}`}>
                  {selectedItem.type.toUpperCase()}
                </span>
                <span className={`text-xs font-mono ${isDark ? 'text-zinc-500' : 'text-gray-500'}`}>
                  Priority {selectedItem.priority}
                </span>
              </div>

              <h4 className={`text-sm font-mono font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                {selectedItem.name}
              </h4>

              <p className={`text-xs leading-relaxed mb-4 ${isDark ? 'text-zinc-400' : 'text-gray-600'}`}>
                {selectedItem.description}
              </p>

              <div className="border-t border-dashed border-zinc-800/30 pt-4 mb-4">
                <span className={`text-[9px] font-mono block mb-1.5 ${isDark ? 'text-zinc-500' : 'text-gray-400'}`}>
                  Python Dotted Path
                </span>
                <div className={`font-mono text-[9px] break-all ${isDark ? 'text-zinc-300' : 'text-gray-800'}`}>
                  {selectedItem.fullName}
                </div>
              </div>

              <div className="space-y-1.5">
                <span className={`text-[9px] font-mono block ${isDark ? 'text-zinc-500' : 'text-gray-400'}`}>
                  Registration Snippet
                </span>
                <div className="font-mono text-[9px] rounded-lg overflow-hidden bg-black/40 border border-zinc-800/40">
                  <CodeBlock language="python" filename="" showLineNumbers={false}>
                    {selectedItem.codeSnippet || ''}
                  </CodeBlock>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export function MiddlewareOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <Layers className="w-4 h-4" />
          <span>MIDDLEWARE / OVERVIEW</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Middleware System &amp; Flows
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Middleware in Aquilia acts as a series of composable wrappers around the request/response lifecycle. Managed by the <DocTerm id="middleware.MiddlewareStack">MiddlewareStack</DocTerm>, every middleware conforms to a strict async signature, enabling deterministic priority execution and scoped filtering.
        </p>
      </div>

      {/* Pipeline Diagram */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Middleware Pipeline Flow</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          <DocTerm id="middleware.MiddlewareStack">MiddlewareStack</DocTerm>.<code className="text-aquilia-500">build_handler()</code> sorts every registered descriptor by <code className="text-aquilia-400">(scope_rank, priority)</code> ascending, then wraps the final handler in <strong>reverse</strong> order — so the <strong>lowest priority number becomes the outermost layer</strong> and runs first on the way in / last on the way out.
        </p>
        <div className="border-l border-white/10 pl-6 py-4 my-6 text-sm text-gray-400 leading-relaxed">
          <p className="mb-4">
            <code className="text-aquilia-400">AquiliaServer._setup_middleware()</code> always registers two internal plumbing middlewares first, regardless of any workspace/module configuration — they are framework infrastructure, not part of the user-facing chain:
          </p>
          <MiddlewareArchitectureDiagram isDark={isDark} />
          <MiddlewarePipelineVisualizer isDark={isDark} />
          <p className="text-xs">
            Note the <strong>overlap</strong>: if you leave <code className="text-aquilia-400">.middleware(...)</code> unset, the server falls back to a hardcoded chain of just <code>ExceptionMiddleware</code> (priority 1) + <code>RequestIdMiddleware</code> (priority 10) — <code>ExceptionMiddleware</code> then sits <em>outside</em> the always-on <code>FaultMiddleware</code> (priority 2) as a last-resort catch-all in case <code>FaultEngine.process()</code> re-raises. See <Link to="/docs/middleware/built-in" className="text-aquilia-400 underline">Built-in Middleware</Link> for the full, source-verified priority table.
          </p>
        </div>
      </section>

      {/* Scope is ordering, not isolation */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-yellow-400 uppercase tracking-wider mb-6`}>Scope Controls Order, Not Which Requests Run It</h2>
        <p className={`mb-4 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          <code className="text-aquilia-500">scope</code> (<code>"global"</code> / <code>"app"</code> / <code>"controller"</code> / <code>"route"</code>) only feeds <code className="text-aquilia-400">MiddlewareStack._sort_middlewares()</code>'s <code>scope_order</code> ranking (<code>global=0, app=1, controller=2, route=3</code>) — it decides <strong>where in the wrapping order</strong> a middleware sits. <code className="text-aquilia-500">build_handler()</code> then wraps <strong>every</strong> registered descriptor unconditionally; nothing in the stack filters a middleware out for requests outside its declared app or route.
        </p>
        <p className={`mb-4 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          <code className="text-aquilia-500">MiddlewareConfig.scope_target</code> (intended for <code>"app:name"</code> / <code>"route:/pattern"</code> pinning) is accepted as a field but is never read by <code>MiddlewareStack</code>, <code>MiddlewareConfig.to_dict()</code>, or <code>AquiliaServer._register_app_middleware()</code> — it has no runtime effect. A middleware registered with <code>scope="app"</code> from one module's manifest still runs for <strong>every</strong> request handled by the process, not just that module's routes.
        </p>
        <div className="text-xs text-orange-400 bg-orange-500/5 p-3 rounded font-mono border border-orange-500/10">
          If you need a middleware to run only for a subset of routes, gate it inside <code>__call__</code> yourself (check <code>request.path</code> / <code>request.state</code>) — don't rely on <code>scope</code> for isolation.
        </div>
      </section>

      {/* Auto-discovery gotcha */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-yellow-400 uppercase tracking-wider mb-6`}>⚠ Auto-Discovery Can Silently Reset Your Manifest Config</h2>
        <p className={`mb-4 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          When <code className="text-aquilia-500">AppManifest.auto_discover</code> is <code>True</code> (the default), <code className="text-aquilia-400">RuntimeRegistry.perform_autodiscovery()</code> scans your module's package for any class named <code>*Middleware</code> or subclassing <DocTerm id="middleware.Middleware">Middleware</DocTerm>. For every discovered class whose import path lives <strong>inside your own module package</strong>, it rebuilds a fresh <code>MiddlewareConfig(class_path=...)</code> with default <code>scope="global"</code>, <code>priority=50</code>, no <code>config</code> — discarding any custom <code>scope</code>, <code>priority</code>, or constructor <code>config</code> you had explicitly set for that same class in <code>middleware=[MiddlewareConfig(...)]</code>.
        </p>
        <p className={`mb-4 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Middleware pointing at classes <strong>outside</strong> your module's package (e.g. built-ins from <code>aquilia.middleware_ext</code>) are left untouched — only local, in-package middleware classes are re-discovered and reset.
        </p>
        <CodeBlock language="python" filename="modules/billing/manifest.py" highlightLines={[8]}>{`from aquilia.manifest import AppManifest, MiddlewareConfig

manifest = AppManifest(
    name="billing",
    version="0.1.0",
    middleware=[
        # Custom priority/config here is DISCARDED at startup unless
        # auto_discover=False, because StripeClientMiddleware lives
        # inside modules.billing (this module's own package).
        MiddlewareConfig(
            class_path="modules.billing.middleware:StripeClientMiddleware",
            priority=30,
            config={"timeout_seconds": 15.0},
        ),
    ],
    auto_discover=False,  # <-- required to keep the custom priority/config
)`}</CodeBlock>
      </section>

      {/* The Middleware Contract */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">The Middleware Contract</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Every middleware in Aquilia must inherit from the <code className="text-aquilia-500">Middleware</code> base class and implement a callable coroutine signature that accepts exactly three parameters. The signature validation is enforced strictly at startup by the <DocTerm id="middleware.MiddlewareStack">MiddlewareStack</DocTerm>:
        </p>

        <CodeBlock language="python" filename="custom_middleware.py" highlightLines={[6, 9, 12]}>{`from aquilia.middleware import Middleware
from aquilia.response import Response

class CustomMiddleware(Middleware):
    async def __call__(self, request, ctx, next_handler) -> Response:
        # 1. Pre-processing: inspect or modify request
        # request.state["my_key"] = "value"

        # 2. Yield control to the next handler
        response = await next_handler(request, ctx)

        # 3. Post-processing: modify response
        # response.headers["X-Custom"] = "done"
        return response`}</CodeBlock>
      </section>

      {/* Short-circuiting */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Short-Circuiting a Request</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          A middleware is never <em>required</em> to call <code className="text-aquilia-500">next_handler</code> — returning a <DocTerm id="response.Response">Response</DocTerm> directly stops the request from reaching any middleware further in (and the controller). <code className="text-aquilia-500">MiddlewareStack._wrap_middleware()</code> only checks that <em>something</em> resolving to a <code>Response</code> came back; it doesn't care whether <code>next_handler</code> was ever awaited. Two built-ins do exactly this:
        </p>

        <div className="border-l border-white/10 pl-6 py-4 my-6 text-sm text-gray-400 space-y-4">
          <div>
            <span className="font-mono text-xs text-white font-bold uppercase">CORSMiddleware — preflight</span>
            <p className="mt-1">
              For <code className="text-aquilia-400">OPTIONS</code> preflight requests it builds and returns the 204 preflight <code>Response</code> straight from <code>_preflight()</code> — <code>next_handler</code> (and therefore your controller) is never invoked for that request.
            </p>
          </div>
          <div>
            <span className="font-mono text-xs text-white font-bold uppercase">CSRFMiddleware — missing/invalid token</span>
            <p className="mt-1">
              On an unsafe method with no valid token, it constructs a <code>403</code> JSON <code>Response</code> with <code>resp._fault = CSRFError(...)</code> attached and returns it immediately — again, without awaiting <code>next_handler</code>.
            </p>
          </div>
        </div>

        <CodeBlock language="python" filename="auth_guard_middleware.py" highlightLines={[7, 8, 9]}>{`from aquilia.middleware import Middleware
from aquilia.response import Response

class RequireApiKeyMiddleware(Middleware):
    async def __call__(self, request, ctx, next_handler) -> Response:
        api_key = request.header("x-api-key")
        if not api_key or api_key not in ("secret-key-1", "secret-key-2"):
            # Short-circuit: never calls next_handler, so the controller
            # and every middleware with a HIGHER priority number never runs.
            return Response.json({"error": "Invalid API key"}, status=401)

        return await next_handler(request, ctx)`}</CodeBlock>
      </section>

      {/* Production composition example */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Composing a Production Chain</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          <code className="text-aquilia-500">MiddlewareChain</code> ships three presets — <code className="text-aquilia-400">.chain()</code> (empty), <code className="text-aquilia-400">.minimal()</code>, <code className="text-aquilia-400">.defaults()</code> (both identical: <code>ExceptionMiddleware</code> priority 1 + <code>RequestIdMiddleware</code> priority 10), and <code className="text-aquilia-400">.production()</code> which additionally adds <code>CompressionMiddleware</code> (priority 15) and <code>TimeoutMiddleware</code> (priority 18, 30s). Start from a preset and append your own entries — the list append order doesn't matter, only <code>priority</code> does:
        </p>

        <CodeBlock language="python" filename="workspace.py" highlightLines={[6, 9, 10, 11]}>{`from aquilia.workspace import Workspace
from aquilia.integrations import MiddlewareChain

workspace = (
    Workspace("myapp")
    .middleware(
        MiddlewareChain
        .production()  # ExceptionMiddleware(1) + RequestIdMiddleware(10)
                        # + CompressionMiddleware(15) + TimeoutMiddleware(18)
        .use("modules.auth.middleware:JwtAuthMiddleware", priority=25)
        .use("aquilia.middleware_ext.RateLimitMiddleware", priority=30,
             default_limit=200, default_window=60.0)
    )
)`}</CodeBlock>
        <p className={`mt-4 text-xs leading-relaxed ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
          Remember: <code className="text-aquilia-400">FaultMiddleware</code> (priority 2, always on) still wraps everything at priority 1 <code>ExceptionMiddleware</code> in this example, so it fires first when a plain <code>Fault</code> subclass is raised. <code>ExceptionMiddleware</code> is your last-resort net if <code>FaultEngine.process()</code> itself re-raises.
        </p>
      </section>

      {/* Workspace Configuration (Global) */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Workspace-Level Middleware Config</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Workspace-level middleware configurations define the global pipeline wrapping all application modules. There are two primary styles to declare these in <code className="text-aquilia-500">workspace.py</code>:
        </p>

        {/* New Style */}
        <div className="mb-8">
          <span className="font-mono text-xs text-green-400 font-bold uppercase tracking-wider block mb-2">1. Fluent MiddlewareChain (Recommended Style)</span>
          <p className="text-sm text-gray-400 mb-4">
            Instantiates the fluent <code className="text-aquilia-400">MiddlewareChain</code> directly on the Workspace. This provides auto-completion, priority order sorting, and inline argument checks:
          </p>
          <CodeBlock language="python" filename="workspace.py" highlightLines={[5, 6, 7]}>{`from aquilia.workspace import Workspace
from aquilia.integrations import MiddlewareChain

workspace = (
    Workspace("myapp")
    .middleware(
        MiddlewareChain()
        .use("aquilia.middleware.ExceptionMiddleware", priority=1)
        .use("aquilia.middleware.RequestIdMiddleware", priority=5)
        .use("modules.auth.middleware:JwtAuthMiddleware", priority=25)
    )
)`}</CodeBlock>
        </div>

        {/* Old Style */}
        <div className="mb-8 border-l-2 border-red-500/30 pl-4 py-2">
          <span className="font-mono text-xs text-red-400 font-bold uppercase tracking-wider block mb-2">⚠️ Integration.middleware_chain() + .integrate() — Does Nothing at Runtime</span>
          <p className="text-sm text-gray-400 mb-4">
            <code className="text-yellow-400">Integration.middleware_chain()</code> is a static builder that returns a plain dict tagged <code className="text-aquilia-400">_integration_type: "middleware_chain"</code>. Passed into <code className="text-aquilia-400">Workspace.integrate()</code>, it is stored at <code className="text-aquilia-300">self._integrations["middleware_chain"]</code>, which serializes into <code className="text-aquilia-300">config["integrations"]["middleware_chain"]</code> — <strong>not</strong> the top-level <code className="text-aquilia-300">config["middleware_chain"]</code> key.
          </p>

          <div className="text-xs text-red-400 mb-4 bg-red-500/5 p-3 rounded font-mono border border-red-500/10 leading-relaxed">
            <strong>WARNING (verified from source):</strong> Every other integration reader (sessions, cache, storage, ...) uses <code>ConfigLoader.get_subsystem_config()</code>, which falls back from <code>get(name)</code> to <code>get(f"integrations.{'{name}'}")</code>. But <code>ConfigLoader.get_middleware_config()</code> is hand-written as <code>self.get("middleware_chain")</code> only — it has <strong>no</strong> fallback to <code>integrations.middleware_chain</code>. Entries configured this way are read by nothing and are silently never instantiated into the running <code>MiddlewareStack</code>. Only <code>Workspace.middleware(MiddlewareChain())</code> (which sets the dedicated top-level <code>_middleware_chain</code> attribute) actually wires middleware. Do not use <code>Integration.middleware_chain()</code> for anything you need to run.
          </div>

          <CodeBlock language="python" filename="workspace_legacy_broken.py" highlightLines={[5, 6, 7]}>{`from aquilia.workspace import Workspace
from aquilia.integrations import Integration

workspace = (
    Workspace("myapp")
    .integrate(
        # This chain is parsed, stored, and then never read again.
        Integration.middleware_chain(
            entries=[
                {"path": "aquilia.middleware.ExceptionMiddleware", "priority": 1},
                {"path": "aquilia.middleware.RequestIdMiddleware", "priority": 5},
            ]
        )
    )
)`}</CodeBlock>
        </div>
      </section>

      {/* Manifest-Based Module Configuration */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Module-Level Middleware Config</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Instead of wrapping the entire workspace, modules declare local middlewares inside their own <code className="text-aquilia-400">manifest.py</code> via <code className="text-aquilia-500">AppManifest</code>.
        </p>

        <div className="mb-8">
          <span className="font-mono text-xs text-green-400 font-bold uppercase tracking-wider block mb-2">1. AppManifest middleware Config (Recommended)</span>
          <p className="text-sm text-gray-400 mb-4">
            Passes list of <code className="text-aquilia-400">MiddlewareConfig</code> objects specifying the class path, target scope, priority, and custom parameters:
          </p>
          <CodeBlock language="python" filename="manifest.py" highlightLines={[6, 7, 8, 9]}>{`from aquilia.manifest import AppManifest, MiddlewareConfig

manifest = AppManifest(
    name="billing",
    version="0.1.0",
    middleware=[
        MiddlewareConfig(
            class_path="modules.billing.middleware:StripeClientMiddleware",
            scope="app",          # Affects wrap ORDER only — see warning above,
                                   # it does NOT limit this middleware to "billing"
            priority=30,
            config={"timeout_seconds": 15.0} # Custom constructor kwargs
        )
    ],
    auto_discover=False,  # keep this exact priority/config — see warning above
)`}</CodeBlock>
        </div>

        <div className="mb-8 border-l-2 border-yellow-500/20 pl-4 py-2">
          <span className="font-mono text-xs text-yellow-400 font-bold uppercase tracking-wider block mb-2">⚠️ AppManifest middlewares list (Deprecated)</span>
          <p className="text-sm text-gray-400 mb-4">
            Legacy manifests declared middleware as a list of tuples containing string paths and configuration dicts.
          </p>
          
          <div className="text-xs text-orange-400 mb-4 bg-orange-500/5 p-3 rounded font-mono border border-orange-500/10">
            <strong>WARNING:</strong> AppManifest will issue a deprecation warning at startup when detecting the <code>middlewares</code> attribute and will auto-convert them internally to MiddlewareConfig instances.
          </div>

          <CodeBlock language="python" filename="manifest_legacy.py" highlightLines={[6]}>{`manifest = AppManifest(
    name="billing",
    version="0.1.0",
    # Legacy tuples configuration
    middlewares=[
        ("modules.billing.middleware:StripeClientMiddleware", {"timeout_seconds": 15.0})
    ]
)`}</CodeBlock>
        </div>
      </section>

      {/* Next Section */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <span />
        <Link to="/docs/middleware/stack" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          MiddlewareStack <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}