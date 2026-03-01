import { Routes, Route } from 'react-router-dom'
import { ThemeProvider } from './context/ThemeContext'
import { DocsLayout } from './components/DocsLayout'
import { LandingPage } from './pages/LandingPage'
import { Changelogs } from './pages/Changelogs'
import { Releases } from './pages/Releases'

// Getting Started
import { IntroductionPage } from './pages/docs/getting-started/Introduction'
import { InstallationPage } from './pages/docs/getting-started/Installation'
import { QuickStartPage } from './pages/docs/getting-started/QuickStart'
import { ArchitecturePage } from './pages/docs/getting-started/Architecture'
import { ProjectStructurePage } from './pages/docs/getting-started/ProjectStructure'

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

// Server
import { ServerOverview } from './pages/docs/server/Overview'
import { ServerASGI } from './pages/docs/server/ASGI'
import { ServerLifecycle } from './pages/docs/server/Lifecycle'

// Config
import { ConfigOverview } from './pages/docs/config/Overview'
import { ConfigWorkspace } from './pages/docs/config/Workspace'
import { ConfigModule } from './pages/docs/config/Module'
import { ConfigIntegrations } from './pages/docs/config/Integrations'

// Request / Response
import { RequestPage } from './pages/docs/request-response/Request'
import { ResponsePage } from './pages/docs/request-response/Response'
import { DataStructuresPage } from './pages/docs/request-response/DataStructures'
import { UploadsPage } from './pages/docs/request-response/Uploads'

// Routing
import { RoutingOverview } from './pages/docs/routing/Overview'

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
import { ModelsFields } from './pages/docs/models/Fields'
import { ModelsQuerySet } from './pages/docs/models/QuerySet'
import { ModelsRelationships } from './pages/docs/models/Relationships'
import { ModelsMigrations } from './pages/docs/models/Migrations'
import { ModelsAdvanced } from './pages/docs/models/Advanced'

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

// Faults
import { FaultsOverview } from './pages/docs/faults/Overview'
import { FaultsEngine } from './pages/docs/faults/Engine'
import { FaultsTaxonomy } from './pages/docs/faults/Taxonomy'
import { FaultsHandlers } from './pages/docs/faults/Handlers'
import { FaultsDomains } from './pages/docs/faults/Domains'

// Cache
import { CacheOverview } from './pages/docs/cache/Overview'
import { CacheService } from './pages/docs/cache/Service'
import { CacheBackends } from './pages/docs/cache/Backends'
import { CacheDecorators } from './pages/docs/cache/Decorators'

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

// Aquilary
import { AquilaryOverview } from './pages/docs/aquilary/Overview'
import { AquilaryManifest } from './pages/docs/aquilary/Manifest'
import { AquilaryRuntime } from './pages/docs/aquilary/Runtime'
import { AquilaryFingerprint } from './pages/docs/aquilary/Fingerprint'

// MLOps
import { MLOpsOverview } from './pages/docs/mlops/Overview'
import { MLOpsTypes } from './pages/docs/mlops/Types'
import { MLOpsAPI } from './pages/docs/mlops/API'
import { MLOpsEngine } from './pages/docs/mlops/Engine'
import { MLOpsModelpack } from './pages/docs/mlops/Modelpack'
import { MLOpsRegistry } from './pages/docs/mlops/Registry'
import { MLOpsRuntime } from './pages/docs/mlops/Runtime'
import { MLOpsServing } from './pages/docs/mlops/Serving'
import { MLOpsOrchestrator } from './pages/docs/mlops/Orchestrator'
import { MLOpsObservability } from './pages/docs/mlops/Observability'
import { MLOpsPlugins } from './pages/docs/mlops/Plugins'
import { MLOpsRelease } from './pages/docs/mlops/Release'
import { MLOpsScheduler } from './pages/docs/mlops/Scheduler'
import { MLOpsSecurity } from './pages/docs/mlops/Security'
import { MLOpsExplain } from './pages/docs/mlops/Explain'
import { MLOpsDeployment } from './pages/docs/mlops/Deployment'
import { MLOpsTutorial } from './pages/docs/mlops/Tutorial'

// CLI
import { CLIOverview } from './pages/docs/cli/Overview'
import { CLICommands } from './pages/docs/cli/Commands'
import { CLIGenerators } from './pages/docs/cli/Generators'
import { CLICoreCommands } from './pages/docs/cli/CoreCommands'
import { CLIDatabaseCommands } from './pages/docs/cli/DatabaseCommands'
import { CLIMLOpsCommands } from './pages/docs/cli/MLOpsCommands'
import { CLIInspectionCommands } from './pages/docs/cli/InspectionCommands'
import { CLIWebSocketCommands } from './pages/docs/cli/WebSocketCommands'
import { CLIDeployCommands } from './pages/docs/cli/DeployCommands'
import { CLIArtifactCommands } from './pages/docs/cli/ArtifactCommands'
import { CLITraceCommands } from './pages/docs/cli/TraceCommands'
import { CLISubsystemCommands } from './pages/docs/cli/SubsystemCommands'

// Testing
import { TestingOverview } from './pages/docs/testing/Overview'
import { TestingClient } from './pages/docs/testing/Client'
import { TestingCases } from './pages/docs/testing/Cases'
import { TestingMocks } from './pages/docs/testing/Mocks'

// Trace
import { TraceOverview } from './pages/docs/trace/Overview'
import { TraceSpans } from './pages/docs/trace/Spans'

export default function App() {
  return (
    <ThemeProvider>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/changelogs" element={<Changelogs />} />
        <Route path="/releases" element={<Releases />} />
        <Route path="/docs" element={<DocsLayout />}>
          <Route index element={<IntroductionPage />} />
          <Route path="installation" element={<InstallationPage />} />
          <Route path="quickstart" element={<QuickStartPage />} />
          <Route path="architecture" element={<ArchitecturePage />} />
          <Route path="project-structure" element={<ProjectStructurePage />} />

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

          {/* Routing */}
          <Route path="routing" element={<RoutingOverview />} />
          <Route path="routing/patterns" element={<RoutingOverview />} />
          <Route path="routing/router" element={<ControllersRouter />} />
          <Route path="routing/urls" element={<RoutingOverview />} />

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
          <Route path="models/fields" element={<ModelsFields />} />
          <Route path="models/queryset" element={<ModelsQuerySet />} />
          <Route path="models/relationships" element={<ModelsRelationships />} />
          <Route path="models/migrations" element={<ModelsMigrations />} />
          <Route path="models/advanced" element={<ModelsAdvanced />} />
          <Route path="models/signals" element={<ModelsAdvanced />} />
          <Route path="models/transactions" element={<ModelsAdvanced />} />
          <Route path="models/aggregation" element={<ModelsAdvanced />} />

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
          <Route path="middleware/stack" element={<MiddlewareStack />} />
          <Route path="middleware/built-in" element={<MiddlewareBuiltIn />} />
          <Route path="middleware/static" element={<MiddlewareExtended />} />
          <Route path="middleware/cors" element={<MiddlewareCORS />} />
          <Route path="middleware/rate-limit" element={<MiddlewareRateLimit />} />
          <Route path="middleware/security" element={<MiddlewareSecurityHeaders />} />

          {/* Aquilary */}
          <Route path="aquilary" element={<AquilaryOverview />} />
          <Route path="aquilary/overview" element={<AquilaryOverview />} />
          <Route path="aquilary/manifest" element={<AquilaryManifest />} />
          <Route path="aquilary/runtime" element={<AquilaryRuntime />} />
          <Route path="aquilary/fingerprint" element={<AquilaryFingerprint />} />

          {/* Effects */}
          <Route path="effects" element={<EffectsOverview />} />
          <Route path="effects/overview" element={<EffectsOverview />} />
          <Route path="effects/dbtx" element={<EffectsDBTx />} />
          <Route path="effects/cache" element={<EffectsCacheEffect />} />

          {/* Faults */}
          <Route path="faults" element={<FaultsOverview />} />
          <Route path="faults/taxonomy" element={<FaultsTaxonomy />} />
          <Route path="faults/engine" element={<FaultsEngine />} />
          <Route path="faults/handlers" element={<FaultsHandlers />} />
          <Route path="faults/domains" element={<FaultsDomains />} />

          {/* Cache */}
          <Route path="cache" element={<CacheOverview />} />
          <Route path="cache/service" element={<CacheService />} />
          <Route path="cache/backends" element={<CacheBackends />} />
          <Route path="cache/decorators" element={<CacheDecorators />} />

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

          {/* MLOps */}
          <Route path="mlops" element={<MLOpsOverview />} />
          <Route path="mlops/types" element={<MLOpsTypes />} />
          <Route path="mlops/api" element={<MLOpsAPI />} />
          <Route path="mlops/engine" element={<MLOpsEngine />} />
          <Route path="mlops/modelpack" element={<MLOpsModelpack />} />
          <Route path="mlops/registry" element={<MLOpsRegistry />} />
          <Route path="mlops/runtime" element={<MLOpsRuntime />} />
          <Route path="mlops/serving" element={<MLOpsServing />} />
          <Route path="mlops/orchestrator" element={<MLOpsOrchestrator />} />
          <Route path="mlops/observability" element={<MLOpsObservability />} />
          <Route path="mlops/plugins" element={<MLOpsPlugins />} />
          <Route path="mlops/release" element={<MLOpsRelease />} />
          <Route path="mlops/scheduler" element={<MLOpsScheduler />} />
          <Route path="mlops/security" element={<MLOpsSecurity />} />
          <Route path="mlops/explain" element={<MLOpsExplain />} />
          <Route path="mlops/deployment" element={<MLOpsDeployment />} />
          <Route path="mlops/tutorial" element={<MLOpsTutorial />} />

          {/* CLI */}
          <Route path="cli" element={<CLIOverview />} />
          <Route path="cli/commands" element={<CLICommands />} />
          <Route path="cli/generators" element={<CLIGenerators />} />
          <Route path="cli/core" element={<CLICoreCommands />} />
          <Route path="cli/database" element={<CLIDatabaseCommands />} />
          <Route path="cli/mlops" element={<CLIMLOpsCommands />} />
          <Route path="cli/inspection" element={<CLIInspectionCommands />} />
          <Route path="cli/websockets" element={<CLIWebSocketCommands />} />
          <Route path="cli/deploy" element={<CLIDeployCommands />} />
          <Route path="cli/artifacts" element={<CLIArtifactCommands />} />
          <Route path="cli/trace" element={<CLITraceCommands />} />
          <Route path="cli/subsystems" element={<CLISubsystemCommands />} />

          {/* Testing */}
          <Route path="testing" element={<TestingOverview />} />
          <Route path="testing/client" element={<TestingClient />} />
          <Route path="testing/cases" element={<TestingCases />} />
          <Route path="testing/mocks" element={<TestingMocks />} />

          {/* OpenAPI */}
          <Route path="openapi" element={<ControllersOpenAPI />} />

          {/* Trace */}
          <Route path="trace" element={<TraceOverview />} />
          <Route path="trace/spans" element={<TraceSpans />} />
        </Route>
      </Routes>
    </ThemeProvider>
  )
}
