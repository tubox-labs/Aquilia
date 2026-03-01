import { Link } from 'react-router-dom'
import { Navbar } from '../components/Navbar'
import { Sidebar } from '../components/Sidebar'
import { useTheme } from '../context/ThemeContext'
import {
  FileText, Tag, GitCommit, Zap, Shield, Database, Box, Layers,
  Terminal, Globe, Brain, Mail, Wrench, ArrowRight, Check,
  Plus, RefreshCw, AlertTriangle, Bug, Cpu, Lock, Workflow,
  Github, Calendar, Hash, Clock, ExternalLink, Sparkles,
  TrendingUp, Package, BookOpen, ChevronRight
} from 'lucide-react'
import { useState, useMemo } from 'react'
import { motion } from 'framer-motion'

interface ChangelogEntry {
  version: string
  date: string
  tag: 'major' | 'minor' | 'patch'
  summary: string
  sections: {
    title: string
    icon: React.ReactNode
    type: 'added' | 'changed' | 'fixed' | 'deprecated' | 'security' | 'breaking'
    items: string[]
  }[]
}

const typeColors: Record<string, { bg: string; text: string; border: string; darkBg: string; darkText: string; darkBorder: string }> = {
  added: { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200', darkBg: 'bg-emerald-500/10', darkText: 'text-emerald-400', darkBorder: 'border-emerald-500/20' },
  changed: { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200', darkBg: 'bg-blue-500/10', darkText: 'text-blue-400', darkBorder: 'border-blue-500/20' },
  fixed: { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200', darkBg: 'bg-amber-500/10', darkText: 'text-amber-400', darkBorder: 'border-amber-500/20' },
  deprecated: { bg: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200', darkBg: 'bg-orange-500/10', darkText: 'text-orange-400', darkBorder: 'border-orange-500/20' },
  security: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200', darkBg: 'bg-red-500/10', darkText: 'text-red-400', darkBorder: 'border-red-500/20' },
  breaking: { bg: 'bg-purple-50', text: 'text-purple-700', border: 'border-purple-200', darkBg: 'bg-purple-500/10', darkText: 'text-purple-400', darkBorder: 'border-purple-500/20' },
}

const typeIcons: Record<string, React.ReactNode> = {
  added: <Plus className="w-3.5 h-3.5" />,
  changed: <RefreshCw className="w-3.5 h-3.5" />,
  fixed: <Bug className="w-3.5 h-3.5" />,
  deprecated: <AlertTriangle className="w-3.5 h-3.5" />,
  security: <Shield className="w-3.5 h-3.5" />,
  breaking: <AlertTriangle className="w-3.5 h-3.5" />,
}

const changelogs: ChangelogEntry[] = [
  {
    version: '1.0.0',
    date: 'February 28, 2026',
    tag: 'major',
    summary: 'Initial production release of Aquilia — a complete, async-native Python web framework with manifest-first architecture, built-in ORM, dependency injection, authentication, MLOps, and more.',
    sections: [
      {
        title: 'Core Framework',
        icon: <Zap className="w-4 h-4" />,
        type: 'added',
        items: [
          'AquiliaServer — high-performance ASGI server with lifecycle hooks, graceful shutdown, and health checks',
          'Manifest-first architecture with two-phase bootstrap → compile → serve pipeline',
          'Request and Response objects with full ASGI support, streaming, and content negotiation',
          'MultiDict, Headers, URL, ParsedContentType, and Range data structures',
          'UploadFile and FormData handling with pluggable upload stores (LocalUploadStore)',
          'HealthRegistry with SubsystemStatus monitoring and health check endpoints',
          'Config and ConfigLoader for YAML/env-based hierarchical configuration',
          'Workspace and Module config builders for Python-native configuration',
          'Integration config builder for third-party service wiring',
          'LifecycleCoordinator and LifecycleManager for phased application startup/shutdown',
        ]
      },
      {
        title: 'Controller System',
        icon: <Layers className="w-4 h-4" />,
        type: 'added',
        items: [
          'Class-based Controller with RequestCtx for type-safe request handling',
          'Full suite of HTTP decorators: @GET, @POST, @PUT, @PATCH, @DELETE, @HEAD, @OPTIONS, @WS, @route',
          'ControllerFactory with InstantiationMode (singleton, per-request, transient)',
          'ControllerEngine and ControllerCompiler for manifest-driven route compilation',
          'ControllerRouter for optimized request dispatch',
          'OpenAPIGenerator and OpenAPIConfig for automatic API documentation',
          'FilterSet, SearchFilter, and OrderingFilter for query filtering',
          'PageNumberPagination, LimitOffsetPagination, CursorPagination, and NoPagination',
          'Content negotiation with JSONRenderer, XMLRenderer, YAMLRenderer, PlainTextRenderer, HTMLRenderer, and ContentNegotiator',
        ]
      },
      {
        title: 'Dependency Injection',
        icon: <Box className="w-4 h-4" />,
        type: 'added',
        items: [
          'Container and DIRegistry with hierarchical scoped DI',
          'ClassProvider, FactoryProvider, and ValueProvider implementations',
          '@service, @factory, @inject decorators and Inject marker',
          'Annotation-driven DI with Dep, Header, Query, and Body extractors',
          'RequestDAG for automatic dependency graph resolution per-request',
          'Singleton, app, request, transient, pooled, and ephemeral lifetime scopes',
          'DI diagnostics and lifecycle management',
        ]
      },
      {
        title: 'Aquilary Registry',
        icon: <Cpu className="w-4 h-4" />,
        type: 'added',
        items: [
          'Aquilary and AquilaryRegistry — manifest-driven app registry with dependency resolution',
          'RuntimeRegistry for runtime component lookup and management',
          'AppContext for scoped application context propagation',
          'RegistryMode for controlling registry behavior (strict, lenient)',
          'RegistryFingerprint for content-addressed fingerprinting of registry state',
          'Structured errors: RegistryError, DependencyCycleError, RouteConflictError, ManifestValidationError',
        ]
      },
      {
        title: 'Model System (ORM)',
        icon: <Database className="w-4 h-4" />,
        type: 'added',
        items: [
          'Pure-Python async ORM with Model, ModelMeta, and ModelRegistry',
          'Comprehensive field types: AutoField, BigAutoField, IntegerField, BigIntegerField, SmallIntegerField, FloatField, DecimalField, CharField, TextField, SlugField, EmailField, URLField, UUIDField, DateField, TimeField, DateTimeField, DurationField, BooleanField, BinaryField, JSONField, and more',
          'Relationship fields: ForeignKey, OneToOneField, ManyToManyField',
          'Advanced fields: ArrayField, HStoreField, GeneratedField, FileField, ImageField',
          'Q objects for complex query composition',
          'Index and UniqueConstraint support',
          'MigrationRunner and MigrationOps with auto-generated migration files',
          'AquiliaDatabase engine with configure_database, get_database, set_database helpers',
          'Multi-backend support: SQLite (aiosqlite), PostgreSQL, MySQL',
          'Legacy AMDL model definition support for backward compatibility',
        ]
      },
      {
        title: 'Blueprints',
        icon: <FileText className="w-4 h-4" />,
        type: 'added',
        items: [
          'Blueprint and BlueprintMeta for model-to-world contracts (serialization/deserialization)',
          'Rich facet system: TextFacet, IntFacet, FloatFacet, DecimalFacet, BoolFacet, DateFacet, TimeFacet, DateTimeFacet, DurationFacet, UUIDFacet, EmailFacet, URLFacet, SlugFacet, IPFacet, ListFacet, DictFacet, JSONFacet, FileFacet, ChoiceFacet',
          'Special facets: Computed, Constant, WriteOnly, ReadOnly, Hidden, Inject',
          'Lens system for field-level projection transformations',
          'Seal-based validation with BlueprintFault, CastFault, SealFault, ImprintFault, ProjectionFault',
          'Automatic schema generation with generate_schema and generate_component_schemas',
          'Integration helpers: is_blueprint_class, render_blueprint_response, bind_blueprint_to_request',
        ]
      },
      {
        title: 'Authentication & Authorization',
        icon: <Lock className="w-4 h-4" />,
        type: 'added',
        items: [
          'Identity model with IdentityStatus and TokenClaims',
          'AuthManager for pluggable authentication flows',
          'TokenManager and KeyRing for JWT/token lifecycle and key management',
          'PasswordHasher with Argon2 and Passlib support',
          'AuthzEngine with RBACEngine and ABACEngine for role/attribute-based access control',
          'OAuth2/OIDC integration support',
          'MFA (Multi-Factor Authentication) support',
          'AuthPrincipal and SessionAuthBridge for session-auth integration',
          'AquilAuthMiddleware and create_auth_middleware_stack',
          'DI integration: register_auth_providers, create_auth_container, AuthConfig',
        ]
      },
      {
        title: 'Session System',
        icon: <Shield className="w-4 h-4" />,
        type: 'added',
        items: [
          'Session, SessionID, SessionPolicy, and SessionEngine',
          'SessionPrincipal with SessionMemoryStore and CookieTransport',
          'Unique decorator syntax: @session, @authenticated, @stateful',
          'Typed SessionState with SessionField (CartState, UserPreferencesState)',
          'SessionContext and SessionGuard with @requires decorator',
          'Built-in guards: AdminGuard, VerifiedEmailGuard',
          'SessionFault and SessionExpiredFault error handling',
        ]
      },
      {
        title: 'Cache System',
        icon: <Zap className="w-4 h-4" />,
        type: 'added',
        items: [
          'CacheService with CacheBackend, CacheEntry, CacheStats, and CacheConfig',
          'Eviction policies: LRU, LFU, TTL, FIFO',
          'Multiple backends: MemoryBackend, RedisBackend, CompositeBackend, NullBackend',
          '@cached, @cache_aside, @invalidate decorators for transparent caching',
          'CacheMiddleware for HTTP-level cache control',
          'Key builders: DefaultKeyBuilder, HashKeyBuilder',
          'Serializers: JsonCacheSerializer, PickleCacheSerializer',
          'Comprehensive fault types: CacheMissFault, CacheConnectionFault, CacheSerializationFault, CacheCapacityFault, and more',
        ]
      },
      {
        title: 'Middleware Stack',
        icon: <Layers className="w-4 h-4" />,
        type: 'added',
        items: [
          'Composable MiddlewareStack with Middleware and Handler base classes',
          'Built-in: RequestIdMiddleware, LoggingMiddleware',
          'CORSMiddleware with full origin, method, and header configuration',
          'CSPMiddleware with CSPPolicy, CSRFMiddleware with csrf_exempt and csrf_token_func',
          'HSTSMiddleware, HTTPSRedirectMiddleware, ProxyFixMiddleware',
          'SecurityHeadersMiddleware for comprehensive security headers',
          'RateLimitMiddleware with configurable RateLimitRule',
          'StaticMiddleware for serving static files',
        ]
      },
      {
        title: 'Fault System',
        icon: <AlertTriangle className="w-4 h-4" />,
        type: 'added',
        items: [
          'Structured Fault base class with FaultContext and FaultEngine',
          'FaultHandler with RecoveryStrategy for resilient error handling',
          'Model-specific faults: ModelFault, AMDLParseFault, ModelNotFoundFault, ModelRegistrationFault',
          'Database faults: MigrationFault, MigrationConflictFault, QueryFault, DatabaseConnectionFault, SchemaFault',
          'Fault domains for scoped error boundaries',
          'Debug pages: DebugPageRenderer, render_debug_exception_page, render_http_error_page, render_welcome_page',
        ]
      },
      {
        title: 'Effects System',
        icon: <Workflow className="w-4 h-4" />,
        type: 'added',
        items: [
          'Effect, EffectProvider, and EffectRegistry for typed side-effect declarations',
          'DBTx effect for managed database transactions',
          'Cache effect for DI-integrated cache operations',
          'Automatic resource lifecycle management within effect scopes',
        ]
      },
      {
        title: 'WebSockets',
        icon: <Globe className="w-4 h-4" />,
        type: 'added',
        items: [
          'SocketController with @OnConnect, @OnDisconnect, @Event decorators',
          'Socket abstraction for send/receive/close operations',
          'AquilaSockets runtime with SocketRouter for namespace-based routing',
          'SocketGuard for WebSocket-level authentication and authorization',
          'Adapter-based architecture for pluggable pub/sub backends',
        ]
      },
      {
        title: 'Templates & Mail',
        icon: <Mail className="w-4 h-4" />,
        type: 'added',
        items: [
          'TemplateEngine with Jinja2 integration and TemplateMiddleware',
          'Template loaders with security sandboxing',
          'AquilaMail: EmailMessage, EmailMultiAlternatives, TemplateMessage',
          'Async mail: send_mail and asend_mail convenience APIs',
          'MailEnvelope with EnvelopeStatus, Priority tracking',
          'MailService with IMailProvider and ProviderResult',
          'Mail fault types: MailSendFault, MailTemplateFault, MailConfigFault, MailSuppressedFault, MailRateLimitFault, MailValidationFault',
        ]
      },
      {
        title: 'MLOps Platform',
        icon: <Brain className="w-4 h-4" />,
        type: 'added',
        items: [
          'Integrated MLOps toolkit for model packaging, registry, serving, and observability',
          'ModelPack builder for containerized model deployment',
          'Model registry with versioning, tagging, and lifecycle management',
          'Runtime backends: ONNX, PyTorch, and custom runtimes',
          'Serving infrastructure with A/B testing and canary rollouts',
          'Orchestrator for pipeline scheduling and execution',
          'Observability with drift detection and model performance monitoring',
          'Explainability integration (SHAP, LIME)',
          'Security policies for model access control',
          'Plugin system for custom runtime extensions',
        ]
      },
      {
        title: 'CLI & Tooling',
        icon: <Terminal className="w-4 h-4" />,
        type: 'added',
        items: [
          'aq CLI entry point with Click-based command framework',
          'Core commands: serve, init, shell, routes, check',
          'Database commands: migrate, makemigrations, dbshell',
          'MLOps commands: model pack, model push, model serve',
          'Inspection commands: show routes, show di, show config',
          'Generator commands: generate controller, generate model, generate blueprint',
          'WebSocket, Deploy, Artifact, Trace, and Subsystem command groups',
        ]
      },
      {
        title: 'Testing Framework',
        icon: <Wrench className="w-4 h-4" />,
        type: 'added',
        items: [
          'TestClient for async HTTP testing without a running server',
          'TestServer and create_test_server for integration testing',
          'AquiliaTestCase, SimpleTestCase, TransactionTestCase, LiveServerTestCase',
          'override_settings context manager for test configuration',
          'Built-in pytest integration with asyncio_mode="auto"',
        ]
      },
      {
        title: 'Trace & Artifacts',
        icon: <Wrench className="w-4 h-4" />,
        type: 'added',
        items: [
          'AquiliaTrace system with .aquilia/ directory for build introspection',
          'TraceManifest, TraceRouteMap, TraceDIGraph for compiled state snapshots',
          'TraceSchemaLedger and TraceLifecycleJournal for schema and lifecycle auditing',
          'TraceConfigSnapshot and TraceDiagnostics for configuration debugging',
          'Artifact system: ArtifactBuilder, ArtifactStore (Memory, Filesystem), ArtifactReader',
          'Typed artifacts: CodeArtifact, ModelArtifact, ConfigArtifact, TemplateArtifact, MigrationArtifact, RegistryArtifact, RouteArtifact, DIGraphArtifact, BundleArtifact',
          'ArtifactEnvelope with ArtifactProvenance and ArtifactIntegrity for supply-chain tracking',
        ]
      },
      {
        title: 'Routing & Discovery',
        icon: <Zap className="w-4 h-4" />,
        type: 'added',
        items: [
          'PatternCompiler, PatternMatcher, and CompiledPattern for high-performance URL matching',
          'PatternTypeRegistry for custom URL parameter types',
          'PackageScanner for automatic controller and service discovery',
          'Flow-based routing with typed, composable pipelines',
        ]
      },
    ]
  },
]

export function Changelogs() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({ '1.0.0': true })
  const [activeFilter, setActiveFilter] = useState<string | null>(null)

  const toggleVersion = (version: string) => {
    setExpandedSections(prev => ({ ...prev, [version]: !prev[version] }))
  }

  const tagColors: Record<string, string> = {
    major: 'bg-aquilia-500/10 text-aquilia-500 border-aquilia-500/20',
    minor: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    patch: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  }

  const stats = useMemo(() => {
    const current = changelogs[0]
    const totalItems = current.sections.reduce((sum, s) => sum + s.items.length, 0)
    const typeBreakdown: Record<string, number> = {}
    current.sections.forEach(s => {
      typeBreakdown[s.type] = (typeBreakdown[s.type] || 0) + s.items.length
    })
    return { totalItems, sectionCount: current.sections.length, typeBreakdown }
  }, [])

  const getFilteredSections = (entry: ChangelogEntry) => {
    if (!activeFilter) return entry.sections
    return entry.sections.filter(s => s.type === activeFilter)
  }

  return (
    <div className="min-h-screen flex flex-col overflow-x-hidden">
      <Navbar onToggleSidebar={() => setIsSidebarOpen(true)} />
      <div className="lg:hidden">
        <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />
      </div>

      <main className="flex-grow pt-16 relative">
        {/* Background */}
        <div className={`fixed inset-0 z-[-1] opacity-20 ${isDark ? '' : 'opacity-5'}`} style={{ backgroundImage: 'linear-gradient(#27272a 1px, transparent 1px), linear-gradient(90deg, #27272a 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
        <div className="fixed inset-0 z-[-1] bg-gradient-to-b from-transparent via-[var(--bg-primary)]/80 to-[var(--bg-primary)]" />

        {/* Hero — full-width, left-aligned */}
        <section className={`relative pt-12 pb-10 overflow-hidden ${isDark ? 'bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-aquilia-900/20 via-black to-black' : ''}`}>
          <div className={`absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]`} />
          <div className="max-w-[90rem] mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <div className={`inline-flex items-center gap-2 mb-4 px-4 py-1.5 rounded-full border text-sm font-medium ${isDark ? 'border-aquilia-500/30 bg-aquilia-500/10 text-aquilia-400' : 'border-aquilia-600/30 bg-aquilia-500/10 text-aquilia-600'}`}>
                <FileText className="w-4 h-4" />
                Changelog
              </div>
              <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight mb-3">
                <span className="gradient-text font-mono">What's New</span>
              </h1>
              <p className={`text-lg max-w-2xl ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                A detailed record of every change, improvement, and fix across all Aquilia releases.
              </p>
            </motion.div>
          </div>
        </section>

        {/* Main Content — two-column full-width */}
        <section className="pb-24">
          <div className="max-w-[90rem] mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex flex-col xl:flex-row gap-8">

              {/* LEFT — Changelog timeline */}
              <div className="flex-1 min-w-0">
                <div className="relative">
                  {/* Timeline line */}
                  <div className={`absolute left-6 top-0 bottom-0 w-px ${isDark ? 'bg-white/10' : 'bg-gray-200'}`} />

                  <div className="space-y-10">
                    {changelogs.map((entry, idx) => {
                      const isExpanded = expandedSections[entry.version] ?? false
                      const filteredSections = getFilteredSections(entry)

                      return (
                        <motion.div
                          key={entry.version}
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: idx * 0.1, duration: 0.5 }}
                          className="relative pl-16"
                        >
                          {/* Timeline dot */}
                          <div className={`absolute left-4 top-2 w-5 h-5 rounded-full border-4 ${isDark ? 'border-[#09090b] bg-aquilia-500' : 'border-white bg-aquilia-500'} shadow-lg shadow-aquilia-500/30`} />

                          {/* Version Header */}
                          <button
                            onClick={() => toggleVersion(entry.version)}
                            className={`w-full text-left group rounded-2xl border p-6 transition-all ${isDark
                              ? 'bg-[#0A0A0A] border-white/10 hover:border-aquilia-500/30'
                              : 'bg-white border-gray-200 hover:border-aquilia-500/30 shadow-sm'
                              }`}
                          >
                            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                              <div className="flex items-center gap-3">
                                <h2 className={`text-2xl font-bold font-mono ${isDark ? 'text-white' : 'text-gray-900'}`}>
                                  v{entry.version}
                                </h2>
                                <span className={`px-2.5 py-0.5 text-xs font-bold uppercase tracking-wider rounded-full border ${tagColors[entry.tag]}`}>
                                  {entry.tag}
                                </span>
                              </div>
                              <div className="flex items-center gap-3">
                                <span className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                                  {entry.date}
                                </span>
                                <GitCommit className={`w-4 h-4 transition-transform duration-300 ${isExpanded ? 'rotate-90' : ''} ${isDark ? 'text-gray-500' : 'text-gray-400'}`} />
                              </div>
                            </div>
                            <p className={`mt-3 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                              {entry.summary}
                            </p>
                          </button>

                          {/* Expandable Sections */}
                          {isExpanded && (
                            <motion.div
                              initial={{ opacity: 0, height: 0 }}
                              animate={{ opacity: 1, height: 'auto' }}
                              transition={{ duration: 0.3 }}
                              className="mt-4 space-y-4"
                            >
                              {filteredSections.length === 0 && (
                                <div className={`text-center py-8 rounded-xl border ${isDark ? 'border-white/5 text-gray-500' : 'border-gray-100 text-gray-400'}`}>
                                  No entries match the selected filter.
                                </div>
                              )}
                              {filteredSections.map((section, sIdx) => {
                                const colors = typeColors[section.type]
                                return (
                                  <motion.div
                                    key={sIdx}
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: sIdx * 0.03, duration: 0.3 }}
                                    className={`rounded-xl border p-5 ${isDark
                                      ? `${colors.darkBg} ${colors.darkBorder} border`
                                      : `${colors.bg} ${colors.border} border`
                                      }`}
                                  >
                                    <div className="flex items-center gap-2 mb-3">
                                      <span className={isDark ? colors.darkText : colors.text}>
                                        {section.icon}
                                      </span>
                                      <h3 className={`font-bold text-sm ${isDark ? 'text-white' : 'text-gray-900'}`}>
                                        {section.title}
                                      </h3>
                                      <span className={`ml-auto flex items-center gap-1 px-2 py-0.5 text-[10px] font-bold uppercase tracking-widest rounded-full ${isDark
                                        ? `${colors.darkBg} ${colors.darkText}`
                                        : `${colors.bg} ${colors.text}`
                                        }`}>
                                        {typeIcons[section.type]}
                                        {section.type}
                                      </span>
                                    </div>
                                    <ul className="space-y-1.5">
                                      {section.items.map((item, iIdx) => (
                                        <li key={iIdx} className="flex items-start gap-2">
                                          <Check className={`w-3.5 h-3.5 mt-0.5 flex-shrink-0 ${isDark ? colors.darkText : colors.text}`} />
                                          <span className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                                            {item}
                                          </span>
                                        </li>
                                      ))}
                                    </ul>
                                  </motion.div>
                                )
                              })}
                            </motion.div>
                          )}
                        </motion.div>
                      )
                    })}
                  </div>
                </div>
              </div>

              {/* RIGHT — Sticky sidebar with contextual info */}
              <div className="xl:w-80 2xl:w-96 flex-shrink-0">
                <div className="xl:sticky xl:top-24 space-y-5">

                  {/* Version Overview */}
                  <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.2, duration: 0.5 }}
                    className={`rounded-2xl border p-5 ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200 shadow-sm'}`}
                  >
                    <h3 className={`text-xs font-bold uppercase tracking-wider mb-4 flex items-center gap-2 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                      <Sparkles className="w-3.5 h-3.5 text-aquilia-500" />
                      Latest Version
                    </h3>
                    <div className="flex items-center gap-3 mb-4">
                      <div className={`text-3xl font-bold font-mono ${isDark ? 'text-white' : 'text-gray-900'}`}>v1.0.0</div>
                      <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded-full bg-aquilia-500 text-black">LATEST</span>
                    </div>
                    <div className="space-y-2.5">
                      <div className="flex items-center gap-2">
                        <Calendar className={`w-3.5 h-3.5 ${isDark ? 'text-gray-500' : 'text-gray-400'}`} />
                        <span className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>February 28, 2026</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Hash className={`w-3.5 h-3.5 ${isDark ? 'text-gray-500' : 'text-gray-400'}`} />
                        <span className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Codename: Genesis</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Clock className={`w-3.5 h-3.5 ${isDark ? 'text-gray-500' : 'text-gray-400'}`} />
                        <span className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Initial Release</span>
                      </div>
                    </div>
                  </motion.div>

                  {/* Stats */}
                  <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3, duration: 0.5 }}
                    className={`rounded-2xl border p-5 ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200 shadow-sm'}`}
                  >
                    <h3 className={`text-xs font-bold uppercase tracking-wider mb-4 flex items-center gap-2 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                      <TrendingUp className="w-3.5 h-3.5 text-aquilia-500" />
                      Release Stats
                    </h3>
                    <div className="grid grid-cols-2 gap-3">
                      {[
                        { value: stats.totalItems, label: 'Total Changes' },
                        { value: stats.sectionCount, label: 'Modules' },
                        { value: '250+', label: 'Public APIs' },
                        { value: '500+', label: 'Commits' },
                      ].map(s => (
                        <div key={s.label} className={`p-3 rounded-xl ${isDark ? 'bg-white/[0.03] border border-white/5' : 'bg-gray-50 border border-gray-100'}`}>
                          <div className={`text-xl font-bold font-mono ${isDark ? 'text-aquilia-400' : 'text-aquilia-600'}`}>{s.value}</div>
                          <div className={`text-[10px] uppercase tracking-wider font-medium mt-0.5 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>{s.label}</div>
                        </div>
                      ))}
                    </div>
                  </motion.div>

                  {/* Filter by Type */}
                  <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.4, duration: 0.5 }}
                    className={`rounded-2xl border p-5 ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200 shadow-sm'}`}
                  >
                    <h3 className={`text-xs font-bold uppercase tracking-wider mb-4 flex items-center gap-2 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                      <Tag className="w-3.5 h-3.5 text-aquilia-500" />
                      Filter by Type
                    </h3>
                    <div className="space-y-1.5">
                      <button
                        onClick={() => setActiveFilter(null)}
                        className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-all ${!activeFilter
                          ? isDark ? 'bg-aquilia-500/10 text-aquilia-400 border border-aquilia-500/20' : 'bg-aquilia-50 text-aquilia-700 border border-aquilia-200'
                          : isDark ? 'text-gray-400 hover:bg-white/5' : 'text-gray-600 hover:bg-gray-50'
                          }`}
                      >
                        <span className="flex items-center gap-2">
                          <Sparkles className="w-3.5 h-3.5" />
                          All Changes
                        </span>
                        <span className={`text-xs font-mono ${isDark ? 'text-gray-600' : 'text-gray-400'}`}>{stats.totalItems}</span>
                      </button>
                      {Object.entries(stats.typeBreakdown).map(([type, count]) => {
                        const colors = typeColors[type]
                        return (
                          <button
                            key={type}
                            onClick={() => setActiveFilter(activeFilter === type ? null : type)}
                            className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-all ${activeFilter === type
                              ? isDark ? `${colors.darkBg} ${colors.darkText} border ${colors.darkBorder}` : `${colors.bg} ${colors.text} border ${colors.border}`
                              : isDark ? 'text-gray-400 hover:bg-white/5' : 'text-gray-600 hover:bg-gray-50'
                              }`}
                          >
                            <span className="flex items-center gap-2">
                              {typeIcons[type]}
                              <span className="capitalize">{type}</span>
                            </span>
                            <span className={`text-xs font-mono ${isDark ? 'text-gray-600' : 'text-gray-400'}`}>{count}</span>
                          </button>
                        )
                      })}
                    </div>
                  </motion.div>

                  {/* Section TOC */}
                  <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.5, duration: 0.5 }}
                    className={`rounded-2xl border p-5 ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200 shadow-sm'}`}
                  >
                    <h3 className={`text-xs font-bold uppercase tracking-wider mb-4 flex items-center gap-2 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                      <BookOpen className="w-3.5 h-3.5 text-aquilia-500" />
                      Sections in v1.0.0
                    </h3>
                    <div className="space-y-0.5 max-h-64 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
                      {changelogs[0].sections.map((section, i) => (
                        <div
                          key={i}
                          className={`flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs transition-colors cursor-default ${isDark ? 'text-gray-400 hover:text-white hover:bg-white/5' : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50'}`}
                        >
                          <span className="text-aquilia-500 flex-shrink-0">{section.icon}</span>
                          <span className="flex-1 truncate">{section.title}</span>
                          <span className={`text-[10px] font-mono flex-shrink-0 ${isDark ? 'text-gray-600' : 'text-gray-400'}`}>{section.items.length}</span>
                        </div>
                      ))}
                    </div>
                  </motion.div>

                  {/* Quick Links */}
                  <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.6, duration: 0.5 }}
                    className={`rounded-2xl border p-5 ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200 shadow-sm'}`}
                  >
                    <h3 className={`text-xs font-bold uppercase tracking-wider mb-4 flex items-center gap-2 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                      <ChevronRight className="w-3.5 h-3.5 text-aquilia-500" />
                      Quick Links
                    </h3>
                    <div className="space-y-2">
                      <Link
                        to="/releases"
                        className={`flex items-center gap-2 px-3 py-2.5 rounded-xl text-sm font-medium transition-all group ${isDark ? 'bg-aquilia-500/5 border border-aquilia-500/10 text-aquilia-400 hover:bg-aquilia-500/10' : 'bg-aquilia-50 border border-aquilia-100 text-aquilia-700 hover:bg-aquilia-100'}`}
                      >
                        <Package className="w-4 h-4" />
                        <span className="flex-1">View Releases</span>
                        <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                      </Link>
                      <Link
                        to="/docs"
                        className={`flex items-center gap-2 px-3 py-2.5 rounded-xl text-sm font-medium transition-all group ${isDark ? 'bg-white/[0.03] border border-white/5 text-gray-300 hover:bg-white/[0.06]' : 'bg-gray-50 border border-gray-100 text-gray-700 hover:bg-gray-100'}`}
                      >
                        <BookOpen className="w-4 h-4" />
                        <span className="flex-1">Read the Docs</span>
                        <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                      </Link>
                      <a
                        href="https://github.com/axiomchronicles/Aquilia"
                        target="_blank"
                        rel="noopener"
                        className={`flex items-center gap-2 px-3 py-2.5 rounded-xl text-sm font-medium transition-all group ${isDark ? 'bg-white/[0.03] border border-white/5 text-gray-300 hover:bg-white/[0.06]' : 'bg-gray-50 border border-gray-100 text-gray-700 hover:bg-gray-100'}`}
                      >
                        <Github className="w-4 h-4" />
                        <span className="flex-1">GitHub Repository</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                  </motion.div>

                  {/* Convention Note */}
                  <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.7, duration: 0.5 }}
                    className={`rounded-2xl border p-5 ${isDark ? 'bg-aquilia-500/5 border-aquilia-500/10' : 'bg-aquilia-50 border-aquilia-100'}`}
                  >
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-lg bg-aquilia-500/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                        <FileText className="w-4 h-4 text-aquilia-500" />
                      </div>
                      <div>
                        <h4 className={`text-sm font-bold mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>Changelog Convention</h4>
                        <p className={`text-xs leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                          This project follows the{' '}
                          <a href="https://keepachangelog.com" target="_blank" rel="noopener" className="text-aquilia-500 hover:underline">Keep a Changelog</a>
                          {' '}specification and{' '}
                          <a href="https://semver.org" target="_blank" rel="noopener" className="text-aquilia-500 hover:underline">Semantic Versioning</a>.
                        </p>
                      </div>
                    </div>
                  </motion.div>

                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className={`border-t backdrop-blur-sm mt-auto ${isDark ? 'border-[var(--border-color)] bg-[var(--bg-card)]/50' : 'border-gray-200 bg-white/50'}`}>
        <div className="max-w-[90rem] mx-auto py-12 px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-8">
            <div className="flex items-center gap-2">
              <img src="/logo.png" alt="Aquilia" className="w-6 h-6 object-contain opacity-80" />
              <span className={`text-sm font-bold tracking-tighter ${isDark ? 'text-white' : 'text-gray-900'}`}>AQUILIA</span>
            </div>
            <div className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
              © 2026 Aquilia Framework. Built for the modern web.
            </div>
            <div className="flex space-x-6">
              <a href="https://github.com/axiomchronicles/Aquilia" target="_blank" rel="noopener" className={`transition-colors ${isDark ? 'text-gray-400 hover:text-aquilia-400' : 'text-gray-400 hover:text-aquilia-600'}`}>
                <Github className="w-5 h-5" />
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
