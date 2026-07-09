import { Routes, Route } from 'react-router-dom'
import { ThemeProvider } from './context/ThemeContext'
import { DocPreviewProvider } from './context/DocPreviewContext'
import { DocPreviewPanel } from './components/docPreview'
import { Chatbox } from './components/Chatbox'
import './data/docEntities'
import { DocsLayout } from './components/DocsLayout'
import { LandingPage } from './pages/LandingPage'
import { Changelogs } from './pages/Changelogs'
import { Releases } from './pages/Releases'
import { BenchmarkPage } from './pages/Benchmark'
import { HelpPage } from './pages/Help'
import { CommunityPage } from './pages/Community'
import { PrivacyPage } from './pages/Privacy'
import { TermsPage } from './pages/Terms'
import { CookiePreferences } from './components/CookiePreferences'
import { NotFoundPage } from './pages/NotFound'
import { ServerErrorPage } from './pages/ServerError'
import { ErrorBoundary } from './components/ErrorBoundary'


// Getting Started
import { IntroductionPage } from './pages/docs/getting-started/Introduction'
import { InstallationPage } from './pages/docs/getting-started/Installation'
import { QuickStartPage } from './pages/docs/getting-started/QuickStart'
import { DeveloperGuidePage } from './pages/docs/getting-started/DeveloperGuide'
import { ArchitecturePage } from './pages/docs/getting-started/Architecture'
import { ProjectStructurePage } from './pages/docs/getting-started/ProjectStructure'
import { AdminSetupPage } from './pages/docs/getting-started/AdminSetup'

// Controllers
import { ControllersOverview } from './pages/docs/controllers/Overview'
import { ControllersDecorators } from './pages/docs/controllers/decorators/Overview'
import { DecoratorGet } from './pages/docs/controllers/decorators/Get'
import { DecoratorPost } from './pages/docs/controllers/decorators/Post'
import { DecoratorPut } from './pages/docs/controllers/decorators/Put'
import { DecoratorPatch } from './pages/docs/controllers/decorators/Patch'
import { DecoratorDelete } from './pages/docs/controllers/decorators/Delete'
import { DecoratorHead } from './pages/docs/controllers/decorators/Head'
import { DecoratorOptions } from './pages/docs/controllers/decorators/Options'
import { DecoratorWS } from './pages/docs/controllers/decorators/WS'
import { DecoratorRoute } from './pages/docs/controllers/decorators/Route'
import { ControllersRequestCtx } from './pages/docs/controllers/RequestCtx'
import { ControllersFactory } from './pages/docs/controllers/Factory'
import { ControllersEngine } from './pages/docs/controllers/Engine'
import { ControllersCompiler } from './pages/docs/controllers/Compiler'
import { ControllersRouter } from './pages/docs/controllers/Router'
import { ControllersOpenAPI } from './pages/docs/controllers/OpenAPI'
import { ControllersValidation } from './pages/docs/controllers/Validation'
import { ControllersPagination } from './pages/docs/controllers/Pagination'
import { ControllersFilters } from './pages/docs/controllers/Filters'
import { ControllersRenderers } from './pages/docs/controllers/Renderers'

// Server
import { ServerOverview } from './pages/docs/server/Overview'
import { ServerASGI } from './pages/docs/server/ASGI'
import { ServerLifecycle } from './pages/docs/server/Lifecycle'

// Config
import { ConfigOverview } from './pages/docs/config/Overview'
import { ConfigWorkspace } from './pages/docs/config/Workspace'
import { ConfigModule } from './pages/docs/config/Module'
import { ConfigIntegrations } from './pages/docs/config/Integrations'
import { ConfigPyConfig } from './pages/docs/config/PyConfig'
import { ConfigDotEnv } from './pages/docs/config/DotEnv'
import { ConfigManifest } from './pages/docs/config/Manifest'

// Request / Response
import { RequestPage } from './pages/docs/request-response/Request'
import { ResponsePage } from './pages/docs/request-response/Response'
import { DataStructuresPage } from './pages/docs/request-response/DataStructures'
import { UploadsPage } from './pages/docs/request-response/Uploads'

// Routing
import { RoutingOverview } from './pages/docs/routing/Overview'
import { RoutingPatterns } from './pages/docs/routing/Patterns'
import { RoutingUrls } from './pages/docs/routing/Urls'

// DI
import { DIOverview } from './pages/docs/di/Overview'
import { DIContainer } from './pages/docs/di/Container'
import { DIProviders } from './pages/docs/di/Providers'
import { DIScopes } from './pages/docs/di/Scopes'
import { DIDecorators } from './pages/docs/di/Decorators'
import { DILifecycle } from './pages/docs/di/Lifecycle'
import { DIDiagnostics } from './pages/docs/di/Diagnostics'
import { DIAdvanced } from './pages/docs/di/DIAdvanced'
import { DIRequestDAG } from './pages/docs/di/RequestDAG'
import { DIExtractors } from './pages/docs/di/Extractors'

// Models
import { ModelsOverview } from './pages/docs/models/Overview'
import { FieldsOverview } from './pages/docs/models/fields/FieldsOverview'
import { NumericFields } from './pages/docs/models/fields/NumericFields'
import { TextFields } from './pages/docs/models/fields/TextFields'
import { DateTimeFields } from './pages/docs/models/fields/DateTimeFields'
import { StructuredFields } from './pages/docs/models/fields/StructuredFields'
import { ModelsQuerySet } from './pages/docs/models/QuerySet'
import { DefiningRelationships } from './pages/docs/models/relationships/DefiningRelationships'
import { HydrationPrimitives } from './pages/docs/models/relationships/HydrationPrimitives'
import { ManyToManyOperations } from './pages/docs/models/relationships/ManyToManyOperations'
import { ModelsMigrations } from './pages/docs/models/Migrations'
import { ModelsAdvanced } from './pages/docs/models/Advanced'
import { ModelsSignals } from './pages/docs/models/Signals'
import { AtomicContexts } from './pages/docs/models/transactions/AtomicContexts'
import { Savepoints } from './pages/docs/models/transactions/Savepoints'
import { Hooks } from './pages/docs/models/transactions/Hooks'
import { ModelsAggregation } from './pages/docs/models/Aggregation'

// Blueprints
import { BlueprintsOverview } from './pages/docs/blueprints/Overview'
import { BlueprintsFacets } from './pages/docs/blueprints/Facets'
import { BlueprintsProjections } from './pages/docs/blueprints/Projections'
import { BlueprintsLenses } from './pages/docs/blueprints/Lenses'
import { BlueprintsSeals } from './pages/docs/blueprints/Seals'
import { BlueprintsAnnotations } from './pages/docs/blueprints/Annotations'
import { BlueprintsIntegration } from './pages/docs/blueprints/Integration'
import { BlueprintsSchemas } from './pages/docs/blueprints/Schemas'
import { BlueprintsFaults } from './pages/docs/blueprints/Faults'

// Database
import { DatabaseOverview } from './pages/docs/database/Overview'
import { DatabaseEngine } from './pages/docs/database/Engine'
import { DatabaseConfigs } from './pages/docs/database/Configs'

// Auth
import { AuthOverview } from './pages/docs/auth/Overview'
import { AuthIdentity } from './pages/docs/auth/Identity'
import { AuthGuards } from './pages/docs/auth/Guards'
import { AuthAdvanced } from './pages/docs/auth/Advanced'
import { AuthZPage } from './pages/docs/auth/AuthZ'
import { AuthCredentials } from './pages/docs/auth/Credentials'
import { AuthManager } from './pages/docs/auth/Manager'
import { AuthOAuth } from './pages/docs/auth/OAuth'
import { AuthMFA } from './pages/docs/auth/MFA'
import { AuthTokens } from './pages/docs/auth/Tokens'
import { AuthStores } from './pages/docs/auth/Stores'
import { AuthFaults } from './pages/docs/auth/Faults'
import { AuthIntegration } from './pages/docs/auth/Integration'

// Sessions
import { SessionsOverview } from './pages/docs/sessions/Overview'
import { SessionsIntegration } from './pages/docs/sessions/Integration'
import { SessionsEngine } from './pages/docs/sessions/Engine'
import { SessionsPolicies } from './pages/docs/sessions/Policies'
import { SessionsStores } from './pages/docs/sessions/Stores'
import { SessionsTransport } from './pages/docs/sessions/Transport'
import { SessionsDecorators } from './pages/docs/sessions/Decorators'
import { SessionsState } from './pages/docs/sessions/State'
import { SessionsGuards } from './pages/docs/sessions/Guards'
import { SessionsFaults } from './pages/docs/sessions/Faults'

// Middleware
import { MiddlewareOverview } from './pages/docs/middleware/Overview'
import { MiddlewareBuiltIn } from './pages/docs/middleware/BuiltIn'
import { MiddlewareExtended } from './pages/docs/middleware/Extended'
import { MiddlewareStack } from './pages/docs/middleware/Stack'
import { MiddlewareCORS } from './pages/docs/middleware/CORS'
import { MiddlewareRateLimit } from './pages/docs/middleware/RateLimit'
import { MiddlewareSecurityHeaders } from './pages/docs/middleware/SecurityHeaders'
import { MiddlewareRequestScope } from './pages/docs/middleware/RequestScope'
import { MiddlewareSession } from './pages/docs/middleware/Session'
import { MiddlewareLogging } from './pages/docs/middleware/Logging'
import { MiddlewareCSP } from './pages/docs/middleware/CSP'
import { MiddlewareCSRF } from './pages/docs/middleware/CSRF'
import { MiddlewareHSTS } from './pages/docs/middleware/HSTS'
import { MiddlewareHTTPSRedirect } from './pages/docs/middleware/HTTPSRedirect'
import { MiddlewareProxyFix } from './pages/docs/middleware/ProxyFix'
import { MiddlewareEffect } from './pages/docs/middleware/EffectMiddleware'


// Faults
import { FaultsOverview } from './pages/docs/faults/Overview'
import { FaultsEngine } from './pages/docs/faults/Engine'
import { FaultsTaxonomy } from './pages/docs/faults/Taxonomy'
import { FaultsHandlers } from './pages/docs/faults/Handlers'
import { FaultsDomains } from './pages/docs/faults/Domains'
import { FaultsAdvanced } from './pages/docs/faults/Advanced'


// Cache
import { CacheOverview } from './pages/docs/cache/Overview'
import { CacheConfiguration } from './pages/docs/cache/Configuration'
import { CacheCLI } from './pages/docs/cache/CLI'
import { CacheService } from './pages/docs/cache/Service'
import { CacheBackends } from './pages/docs/cache/Backends'
import { CacheDecorators } from './pages/docs/cache/Decorators'
import { CacheAPIReference } from './pages/docs/cache/APIReference'

// HTTP Client
import { HTTPOverview } from './pages/docs/http/Overview'
import { HTTPClient } from './pages/docs/http/Client'
import { HTTPSessions } from './pages/docs/http/Sessions'
import { HTTPTransport } from './pages/docs/http/Transport'
import { HTTPAdvanced } from './pages/docs/http/Advanced'
import { HTTPFaults } from './pages/docs/http/Faults'
import { HTTPIntegration } from './pages/docs/http/Integration'
import { HTTPAPIRequest } from './pages/docs/http/api/Request'
import { HTTPAPIResponse } from './pages/docs/http/api/Response'
import { HTTPAPIAuth } from './pages/docs/http/api/Auth'
import { HTTPAPICookies } from './pages/docs/http/api/Cookies'
import { HTTPAPIMiddleware } from './pages/docs/http/api/Middleware'
import { HTTPAPIMultipart } from './pages/docs/http/api/Multipart'
import { HTTPAPIStreaming } from './pages/docs/http/api/Streaming'

// I18n
import { I18nOverview } from './pages/docs/i18n/Overview'
import { I18nArchitecture } from './pages/docs/i18n/Architecture'
import { I18nConfiguration } from './pages/docs/i18n/Configuration'
import { I18nIntegration } from './pages/docs/i18n/Integration'
import { I18nAPIReference } from './pages/docs/i18n/APIReference'
import { I18nCLI } from './pages/docs/i18n/CLI'
import { I18nEdgeCases } from './pages/docs/i18n/EdgeCases'
import { I18nTroubleshooting } from './pages/docs/i18n/Troubleshooting'

// WebSockets
import { WebSocketsOverview } from './pages/docs/websockets/Overview'
import { WebSocketControllers } from './pages/docs/websockets/Controllers'
import { WebSocketRuntime } from './pages/docs/websockets/Runtime'
import { WebSocketAdapters } from './pages/docs/websockets/Adapters'

// Templates
import { TemplatesOverview } from './pages/docs/templates/Overview'
import { TemplatesEngine } from './pages/docs/templates/Engine'
import { TemplatesLoaders } from './pages/docs/templates/Loaders'
import { TemplatesSecurity } from './pages/docs/templates/Security'

// Mail
import { MailOverview } from './pages/docs/mail/Overview'
import { MailService } from './pages/docs/mail/Service'
import { MailProviders } from './pages/docs/mail/Providers'
import { MailTemplates } from './pages/docs/mail/Templates'

// Effects
import { EffectsOverview } from './pages/docs/effects/Overview'
import { EffectsDBTx } from './pages/docs/effects/DBTx'
import { EffectsCacheEffect } from './pages/docs/effects/CacheEffect'
import { EffectsBuiltIn } from './pages/docs/effects/BuiltIn'
import { EffectsQueueEffect } from './pages/docs/effects/QueueEffect'
import { EffectsHTTPEffect } from './pages/docs/effects/HTTPEffect'
import { EffectsStorageEffect } from './pages/docs/effects/StorageEffect'
import { EffectsCustomEffects } from './pages/docs/effects/CustomEffects'


// Aquilary
import { AquilaryOverview } from './pages/docs/aquilary/Overview'
import { AquilaryManifest } from './pages/docs/aquilary/Manifest'
import { AquilaryRuntime } from './pages/docs/aquilary/Runtime'
import { AquilaryFingerprint } from './pages/docs/aquilary/Fingerprint'


// CLI
import { CLIOverview } from './pages/docs/cli/Overview'
import { CLICommands } from './pages/docs/cli/Commands'
import { CLIGenerators } from './pages/docs/cli/Generators'
import { CLICoreCommands } from './pages/docs/cli/CoreCommands'
import { CLIDatabaseCommands } from './pages/docs/cli/DatabaseCommands'
import { CLIInspectionCommands } from './pages/docs/cli/InspectionCommands'
import { CLIWebSocketCommands } from './pages/docs/cli/WebSocketCommands'
import { CLIDeployCommands } from './pages/docs/cli/DeployCommands'
import { CLIArtifactCommands } from './pages/docs/cli/ArtifactCommands'
import { CLISubsystemCommands } from './pages/docs/cli/SubsystemCommands'

// Testing
import { TestingOverview } from './pages/docs/testing/Overview'
import { TestingClient } from './pages/docs/testing/Client'
import { TestingCases } from './pages/docs/testing/Cases'
import { TestingMocks } from './pages/docs/testing/Mocks'
import { TestingRunner } from './pages/docs/testing/Runner'



// Tasks
import { TasksOverview } from './pages/docs/tasks/Overview'
import { TasksAPI } from './pages/docs/tasks/API'
import { TasksConfiguration } from './pages/docs/tasks/Configuration'
import { TasksRetry } from './pages/docs/tasks/Retry'
import { TasksScheduling } from './pages/docs/tasks/Scheduling'
import { TasksController } from './pages/docs/tasks/Controller'

// Storage
import { StorageOverview } from './pages/docs/storage/Overview'
import { StorageAPI } from './pages/docs/storage/API'
import { StorageConfiguration } from './pages/docs/storage/Configuration'
import { StorageBackends } from './pages/docs/storage/Backends'
import { StorageController } from './pages/docs/storage/Controller'

// SQLite
import { SqliteOverview } from './pages/docs/sqlite/Overview'
import { SqliteAPI } from './pages/docs/sqlite/API'
import { SqlitePool } from './pages/docs/sqlite/Pool'
import { SqliteTransactions } from './pages/docs/sqlite/Transactions'
import { SqliteController } from './pages/docs/sqlite/Controller'

// Filesystem
import { FilesystemOverview } from './pages/docs/filesystem/Overview'
import { FilesystemAPI } from './pages/docs/filesystem/API'
import { FilesystemOperations } from './pages/docs/filesystem/Operations'
import { FilesystemController } from './pages/docs/filesystem/Controller'

import { PrintAllDocs } from './pages/PrintAllDocs'

export default function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <DocPreviewProvider>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/print-docs" element={<PrintAllDocs />} />
        <Route path="/benchmark" element={<BenchmarkPage />} />
        <Route path="/changelogs" element={<Changelogs />} />
        <Route path="/releases" element={<Releases />} />
        <Route path="/help" element={<HelpPage />} />
        <Route path="/community" element={<CommunityPage />} />
        <Route path="/privacy" element={<PrivacyPage />} />
        <Route path="/terms" element={<TermsPage />} />
        <Route path="/docs" element={<DocsLayout />}>
          <Route index element={<IntroductionPage />} />
          <Route path="installation" element={<InstallationPage />} />
          <Route path="quickstart" element={<QuickStartPage />} />
          <Route path="developer-guide" element={<DeveloperGuidePage />} />
          <Route path="architecture" element={<ArchitecturePage />} />
          <Route path="project-structure" element={<ProjectStructurePage />} />
          <Route path="admin-panel" element={<AdminSetupPage />} />

          {/* Server */}
          <Route path="server" element={<ServerOverview />} />
          <Route path="server/aquilia-server" element={<ServerOverview />} />
          <Route path="server/asgi" element={<ServerASGI />} />
          <Route path="server/lifecycle" element={<ServerLifecycle />} />

          {/* Config */}
          <Route path="config" element={<ConfigOverview />} />
          <Route path="config/loader" element={<ConfigOverview />} />
          <Route path="config/workspace" element={<ConfigWorkspace />} />
          <Route path="config/module" element={<ConfigModule />} />
          <Route path="config/integrations" element={<ConfigIntegrations />} />
          <Route path="config/pyconfig" element={<ConfigPyConfig />} />
          <Route path="config/dotenv" element={<ConfigDotEnv />} />
          <Route path="config/manifest" element={<ConfigManifest />} />

          {/* Request/Response */}
          <Route path="request-response" element={<RequestPage />} />
          <Route path="request-response/request" element={<RequestPage />} />
          <Route path="request-response/response" element={<ResponsePage />} />
          <Route path="request-response/data-structures" element={<DataStructuresPage />} />
          <Route path="request-response/uploads" element={<UploadsPage />} />

          {/* Controllers */}
          <Route path="controllers" element={<ControllersOverview />} />
          <Route path="controllers/overview" element={<ControllersOverview />} />
          <Route path="controllers/decorators" element={<ControllersDecorators />} />
          <Route path="controllers/decorators/get" element={<DecoratorGet />} />
          <Route path="controllers/decorators/post" element={<DecoratorPost />} />
          <Route path="controllers/decorators/put" element={<DecoratorPut />} />
          <Route path="controllers/decorators/patch" element={<DecoratorPatch />} />
          <Route path="controllers/decorators/delete" element={<DecoratorDelete />} />
          <Route path="controllers/decorators/head" element={<DecoratorHead />} />
          <Route path="controllers/decorators/options" element={<DecoratorOptions />} />
          <Route path="controllers/decorators/ws" element={<DecoratorWS />} />
          <Route path="controllers/decorators/route" element={<DecoratorRoute />} />
          <Route path="controllers/request-ctx" element={<ControllersRequestCtx />} />
          <Route path="controllers/factory" element={<ControllersFactory />} />
          <Route path="controllers/engine" element={<ControllersEngine />} />
          <Route path="controllers/compiler" element={<ControllersCompiler />} />
          <Route path="controllers/router" element={<ControllersRouter />} />
          <Route path="controllers/openapi" element={<ControllersOpenAPI />} />
          <Route path="controllers/validation" element={<ControllersValidation />} />
          <Route path="controllers/pagination" element={<ControllersPagination />} />
          <Route path="controllers/filters" element={<ControllersFilters />} />
          <Route path="controllers/renderers" element={<ControllersRenderers />} />

          {/* Routing */}
          <Route path="routing" element={<RoutingOverview />} />
          <Route path="routing/patterns" element={<RoutingPatterns />} />
          <Route path="routing/router" element={<ControllersRouter />} />
          <Route path="routing/urls" element={<RoutingUrls />} />

          {/* DI */}
          <Route path="di" element={<DIOverview />} />
          <Route path="di/container" element={<DIContainer />} />
          <Route path="di/providers" element={<DIProviders />} />
          <Route path="di/scopes" element={<DIScopes />} />
          <Route path="di/decorators" element={<DIDecorators />} />
          <Route path="di/lifecycle" element={<DILifecycle />} />
          <Route path="di/request-dag" element={<DIRequestDAG />} />
          <Route path="di/extractors" element={<DIExtractors />} />
          <Route path="di/diagnostics" element={<DIDiagnostics />} />
          <Route path="di/advanced" element={<DIAdvanced />} />

          {/* Models */}
          <Route path="models" element={<ModelsOverview />} />
          <Route path="models/overview" element={<ModelsOverview />} />
          <Route path="models/defining" element={<ModelsOverview />} />
          
          {/* Fields Subpages */}
          <Route path="models/fields" element={<FieldsOverview />} />
          <Route path="models/fields/overview" element={<FieldsOverview />} />
          <Route path="models/fields/numeric" element={<NumericFields />} />
          <Route path="models/fields/text" element={<TextFields />} />
          <Route path="models/fields/datetime" element={<DateTimeFields />} />
          <Route path="models/fields/structured" element={<StructuredFields />} />
          
          <Route path="models/queryset" element={<ModelsQuerySet />} />
          
          {/* Relationships Subpages */}
          <Route path="models/relationships" element={<DefiningRelationships />} />
          <Route path="models/relationships/defining" element={<DefiningRelationships />} />
          <Route path="models/relationships/hydration" element={<HydrationPrimitives />} />
          <Route path="models/relationships/m2m" element={<ManyToManyOperations />} />
          
          <Route path="models/migrations" element={<ModelsMigrations />} />
          <Route path="models/advanced" element={<ModelsAdvanced />} />
          <Route path="models/signals" element={<ModelsSignals />} />
          
          {/* Transactions Subpages */}
          <Route path="models/transactions" element={<AtomicContexts />} />
          <Route path="models/transactions/atomic" element={<AtomicContexts />} />
          <Route path="models/transactions/savepoints" element={<Savepoints />} />
          <Route path="models/transactions/hooks" element={<Hooks />} />
          
          <Route path="models/aggregation" element={<ModelsAggregation />} />

          {/* Blueprints */}
          <Route path="blueprints" element={<BlueprintsOverview />} />
          <Route path="blueprints/overview" element={<BlueprintsOverview />} />
          <Route path="blueprints/facets" element={<BlueprintsFacets />} />
          <Route path="blueprints/projections" element={<BlueprintsProjections />} />
          <Route path="blueprints/lenses" element={<BlueprintsLenses />} />
          <Route path="blueprints/seals" element={<BlueprintsSeals />} />
          <Route path="blueprints/annotations" element={<BlueprintsAnnotations />} />
          <Route path="blueprints/integration" element={<BlueprintsIntegration />} />
          <Route path="blueprints/schemas" element={<BlueprintsSchemas />} />
          <Route path="blueprints/faults" element={<BlueprintsFaults />} />

          {/* Database */}
          <Route path="database" element={<DatabaseOverview />} />
          <Route path="database/engine" element={<DatabaseEngine />} />
          <Route path="database/configs" element={<DatabaseConfigs />} />
          <Route path="database/sqlite" element={<DatabaseOverview />} />
          <Route path="database/postgresql" element={<DatabaseOverview />} />
          <Route path="database/mysql" element={<DatabaseOverview />} />

          {/* Auth */}
          <Route path="auth" element={<AuthOverview />} />
          <Route path="auth/identity" element={<AuthIdentity />} />
          <Route path="auth/credentials" element={<AuthCredentials />} />
          <Route path="auth/manager" element={<AuthManager />} />
          <Route path="auth/oauth" element={<AuthOAuth />} />
          <Route path="auth/mfa" element={<AuthMFA />} />
          <Route path="auth/tokens" element={<AuthTokens />} />
          <Route path="auth/stores" element={<AuthStores />} />
          <Route path="auth/faults" element={<AuthFaults />} />
          <Route path="auth/guards" element={<AuthGuards />} />
          <Route path="auth/integration" element={<AuthIntegration />} />
          <Route path="auth/advanced" element={<AuthAdvanced />} />
          <Route path="authz" element={<AuthZPage />} />
          <Route path="authz/rbac" element={<AuthZPage />} />
          <Route path="authz/abac" element={<AuthZPage />} />
          <Route path="authz/policies" element={<AuthZPage />} />

          {/* Sessions */}
          <Route path="sessions" element={<SessionsOverview />} />
          <Route path="sessions/overview" element={<SessionsOverview />} />
          <Route path="sessions/integration" element={<SessionsIntegration />} />
          <Route path="sessions/engine" element={<SessionsEngine />} />
          <Route path="sessions/policies" element={<SessionsPolicies />} />
          <Route path="sessions/stores" element={<SessionsStores />} />
          <Route path="sessions/transport" element={<SessionsTransport />} />
          <Route path="sessions/decorators" element={<SessionsDecorators />} />
          <Route path="sessions/state" element={<SessionsState />} />
          <Route path="sessions/guards" element={<SessionsGuards />} />
          <Route path="sessions/faults" element={<SessionsFaults />} />

          {/* Middleware */}
          <Route path="middleware" element={<MiddlewareOverview />} />
          <Route path="middleware/overview" element={<MiddlewareOverview />} />
          <Route path="middleware/stack" element={<MiddlewareStack />} />
          <Route path="middleware/built-in" element={<MiddlewareBuiltIn />} />
          <Route path="middleware/static" element={<MiddlewareExtended />} />
          <Route path="middleware/cors" element={<MiddlewareCORS />} />
          <Route path="middleware/rate-limit" element={<MiddlewareRateLimit />} />
          <Route path="middleware/security" element={<MiddlewareSecurityHeaders />} />
          <Route path="middleware/request-scope" element={<MiddlewareRequestScope />} />
          <Route path="middleware/session" element={<MiddlewareSession />} />
          <Route path="middleware/logging" element={<MiddlewareLogging />} />
          <Route path="middleware/csp" element={<MiddlewareCSP />} />
          <Route path="middleware/csrf" element={<MiddlewareCSRF />} />
          <Route path="middleware/hsts" element={<MiddlewareHSTS />} />
          <Route path="middleware/https-redirect" element={<MiddlewareHTTPSRedirect />} />
          <Route path="middleware/proxy-fix" element={<MiddlewareProxyFix />} />
          <Route path="middleware/effect" element={<MiddlewareEffect />} />


          {/* Aquilary */}
          <Route path="aquilary" element={<AquilaryOverview />} />
          <Route path="aquilary/overview" element={<AquilaryOverview />} />
          <Route path="aquilary/manifest" element={<AquilaryManifest />} />
          <Route path="aquilary/runtime" element={<AquilaryRuntime />} />
          <Route path="aquilary/fingerprint" element={<AquilaryFingerprint />} />

          {/* Effects */}
          <Route path="effects" element={<EffectsOverview />} />
          <Route path="effects/overview" element={<EffectsOverview />} />
          <Route path="effects/built-in" element={<EffectsBuiltIn />} />
          <Route path="effects/dbtx" element={<EffectsDBTx />} />
          <Route path="effects/cache" element={<EffectsCacheEffect />} />
          <Route path="effects/queue" element={<EffectsQueueEffect />} />
          <Route path="effects/http" element={<EffectsHTTPEffect />} />
          <Route path="effects/storage" element={<EffectsStorageEffect />} />
          <Route path="effects/custom" element={<EffectsCustomEffects />} />


          {/* Faults */}
          <Route path="faults" element={<FaultsOverview />} />
          <Route path="faults/taxonomy" element={<FaultsTaxonomy />} />
          <Route path="faults/engine" element={<FaultsEngine />} />
          <Route path="faults/handlers" element={<FaultsHandlers />} />
          <Route path="faults/domains" element={<FaultsDomains />} />
          <Route path="faults/advanced" element={<FaultsAdvanced />} />


          {/* Cache */}
          <Route path="cache" element={<CacheOverview />} />
          <Route path="cache/configuration" element={<CacheConfiguration />} />
          <Route path="cache/cli" element={<CacheCLI />} />
          <Route path="cache/service" element={<CacheService />} />
          <Route path="cache/backends" element={<CacheBackends />} />
          <Route path="cache/decorators" element={<CacheDecorators />} />
          <Route path="cache/api-reference" element={<CacheAPIReference />} />

          {/* HTTP Client */}
          <Route path="http" element={<HTTPOverview />} />
          <Route path="http/client" element={<HTTPClient />} />
          <Route path="http/sessions" element={<HTTPSessions />} />
          <Route path="http/transport" element={<HTTPTransport />} />
          <Route path="http/advanced" element={<HTTPAdvanced />} />
          <Route path="http/faults" element={<HTTPFaults />} />
          <Route path="http/integration" element={<HTTPIntegration />} />
          <Route path="http/api" element={<HTTPAPIRequest />} />
          <Route path="http/api/request" element={<HTTPAPIRequest />} />
          <Route path="http/api/response" element={<HTTPAPIResponse />} />
          <Route path="http/api/auth" element={<HTTPAPIAuth />} />
          <Route path="http/api/cookies" element={<HTTPAPICookies />} />
          <Route path="http/api/middleware" element={<HTTPAPIMiddleware />} />
          <Route path="http/api/multipart" element={<HTTPAPIMultipart />} />
          <Route path="http/api/streaming" element={<HTTPAPIStreaming />} />

          {/* I18n */}
          <Route path="i18n" element={<I18nOverview />} />
          <Route path="i18n/overview" element={<I18nOverview />} />
          <Route path="i18n/architecture" element={<I18nArchitecture />} />
          <Route path="i18n/configuration" element={<I18nConfiguration />} />
          <Route path="i18n/integration" element={<I18nIntegration />} />
          <Route path="i18n/api-reference" element={<I18nAPIReference />} />
          <Route path="i18n/cli" element={<I18nCLI />} />
          <Route path="i18n/edge-cases" element={<I18nEdgeCases />} />
          <Route path="i18n/troubleshooting" element={<I18nTroubleshooting />} />

          {/* i8n alias routes */}
          <Route path="i8n" element={<I18nOverview />} />
          <Route path="i8n/overview" element={<I18nOverview />} />
          <Route path="i8n/architecture" element={<I18nArchitecture />} />
          <Route path="i8n/configuration" element={<I18nConfiguration />} />
          <Route path="i8n/integration" element={<I18nIntegration />} />
          <Route path="i8n/api-reference" element={<I18nAPIReference />} />
          <Route path="i8n/cli" element={<I18nCLI />} />
          <Route path="i8n/edge-cases" element={<I18nEdgeCases />} />
          <Route path="i8n/troubleshooting" element={<I18nTroubleshooting />} />

          {/* WebSockets */}
          <Route path="websockets" element={<WebSocketsOverview />} />
          <Route path="websockets/controllers" element={<WebSocketControllers />} />
          <Route path="websockets/runtime" element={<WebSocketRuntime />} />
          <Route path="websockets/adapters" element={<WebSocketAdapters />} />

          {/* Templates */}
          <Route path="templates" element={<TemplatesOverview />} />
          <Route path="templates/engine" element={<TemplatesEngine />} />
          <Route path="templates/loaders" element={<TemplatesLoaders />} />
          <Route path="templates/security" element={<TemplatesSecurity />} />

          {/* Mail */}
          <Route path="mail" element={<MailOverview />} />
          <Route path="mail/service" element={<MailService />} />
          <Route path="mail/providers" element={<MailProviders />} />
          <Route path="mail/templates" element={<MailTemplates />} />



          {/* CLI */}
          <Route path="cli" element={<CLIOverview />} />
          <Route path="cli/commands" element={<CLICommands />} />
          <Route path="cli/generators" element={<CLIGenerators />} />
          <Route path="cli/core" element={<CLICoreCommands />} />
          <Route path="cli/database" element={<CLIDatabaseCommands />} />
          <Route path="cli/inspection" element={<CLIInspectionCommands />} />
          <Route path="cli/websockets" element={<CLIWebSocketCommands />} />
          <Route path="cli/deploy" element={<CLIDeployCommands />} />
          <Route path="cli/artifacts" element={<CLIArtifactCommands />} />
          <Route path="cli/subsystems" element={<CLISubsystemCommands />} />

          {/* Testing */}
          <Route path="testing" element={<TestingOverview />} />
          <Route path="testing/client" element={<TestingClient />} />
          <Route path="testing/cases" element={<TestingCases />} />
          <Route path="testing/mocks" element={<TestingMocks />} />
          <Route path="testing/runner" element={<TestingRunner />} />

          {/* OpenAPI */}
          <Route path="openapi" element={<ControllersOpenAPI />} />



          {/* Tasks */}
          <Route path="tasks" element={<TasksOverview />} />
          <Route path="tasks/overview" element={<TasksOverview />} />
          <Route path="tasks/api" element={<TasksAPI />} />
          <Route path="tasks/configuration" element={<TasksConfiguration />} />
          <Route path="tasks/retry" element={<TasksRetry />} />
          <Route path="tasks/scheduling" element={<TasksScheduling />} />
          <Route path="tasks/controller" element={<TasksController />} />

          {/* Storage */}
          <Route path="storage" element={<StorageOverview />} />
          <Route path="storage/overview" element={<StorageOverview />} />
          <Route path="storage/api" element={<StorageAPI />} />
          <Route path="storage/configuration" element={<StorageConfiguration />} />
          <Route path="storage/backends" element={<StorageBackends />} />
          <Route path="storage/controller" element={<StorageController />} />

          {/* SQLite */}
          <Route path="sqlite" element={<SqliteOverview />} />
          <Route path="sqlite/overview" element={<SqliteOverview />} />
          <Route path="sqlite/api" element={<SqliteAPI />} />
          <Route path="sqlite/pool" element={<SqlitePool />} />
          <Route path="sqlite/transactions" element={<SqliteTransactions />} />
          <Route path="sqlite/controller" element={<SqliteController />} />

          {/* Filesystem */}
          <Route path="filesystem" element={<FilesystemOverview />} />
          <Route path="filesystem/overview" element={<FilesystemOverview />} />
          <Route path="filesystem/api" element={<FilesystemAPI />} />
          <Route path="filesystem/operations" element={<FilesystemOperations />} />
          <Route path="filesystem/controller" element={<FilesystemController />} />

          {/* Docs Wildcard 404 */}
          <Route path="*" element={<NotFoundPage />} />
        </Route>

        <Route path="/500" element={<ServerErrorPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
      <DocPreviewPanel />
      <Chatbox />
      <CookiePreferences />
      </DocPreviewProvider>
    </ThemeProvider>
    </ErrorBoundary>
  )
}
