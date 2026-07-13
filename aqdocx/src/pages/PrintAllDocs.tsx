import { useEffect } from 'react'
import { useTheme } from '../context/ThemeContext'
import { Releases } from './Releases'
import { Changelogs } from './Changelogs'

import { IntroductionPage } from './docs/getting-started/Introduction'
import { InstallationPage } from './docs/getting-started/Installation'
import { QuickStartPage } from './docs/getting-started/QuickStart'
import { DeveloperGuidePage } from './docs/getting-started/DeveloperGuide'
import { ArchitecturePage } from './docs/getting-started/Architecture'
import { ProjectStructurePage } from './docs/getting-started/ProjectStructure'
import { AdminSetupPage } from './docs/getting-started/AdminSetup'
import { TutorialOverview } from './docs/tutorials/Overview'
import { TodoTutorialPage } from './docs/tutorials/TodoTutorial'
import { AuthTutorialPage } from './docs/tutorials/AuthTutorial'
import { ServerOverview } from './docs/server/Overview'
import { ServerASGI } from './docs/server/ASGI'
import { ServerLifecycle } from './docs/server/Lifecycle'
import { ConfigOverview } from './docs/config/Overview'
import { ConfigPyConfig } from './docs/config/PyConfig'
import { ConfigDotEnv } from './docs/config/DotEnv'
import { ConfigWorkspace } from './docs/config/Workspace'
import { ConfigModule } from './docs/config/Module'
import { ConfigManifest } from './docs/config/Manifest'
import { ConfigIntegrations } from './docs/config/Integrations'
import { RequestPage } from './docs/request-response/Request'
import { ResponsePage } from './docs/request-response/Response'
import { DataStructuresPage } from './docs/request-response/DataStructures'
import { UploadsPage } from './docs/request-response/Uploads'
import { ControllersOverview } from './docs/controllers/Overview'
import { ControllersRequestCtx } from './docs/controllers/RequestCtx'
import { ControllersFactory } from './docs/controllers/Factory'
import { ControllersEngine } from './docs/controllers/Engine'
import { ControllersCompiler } from './docs/controllers/Compiler'
import { ControllersRouter } from './docs/controllers/Router'
import { ControllersOpenAPI } from './docs/controllers/OpenAPI'
import { ControllersValidation } from './docs/controllers/Validation'
import { ControllersPagination } from './docs/controllers/Pagination'
import { ControllersFilters } from './docs/controllers/Filters'
import { ControllersRenderers } from './docs/controllers/Renderers'
import { ControllersDecorators } from './docs/controllers/decorators/Overview'
import { DecoratorGet } from './docs/controllers/decorators/Get'
import { DecoratorPost } from './docs/controllers/decorators/Post'
import { DecoratorPut } from './docs/controllers/decorators/Put'
import { DecoratorPatch } from './docs/controllers/decorators/Patch'
import { DecoratorDelete } from './docs/controllers/decorators/Delete'
import { DecoratorHead } from './docs/controllers/decorators/Head'
import { DecoratorOptions } from './docs/controllers/decorators/Options'
import { DecoratorWS } from './docs/controllers/decorators/WS'
import { DecoratorRoute } from './docs/controllers/decorators/Route'
import { RoutingOverview } from './docs/routing/Overview'
import { RoutingPatterns } from './docs/routing/Patterns'
import { RoutingUrls } from './docs/routing/Urls'
import { DIOverview } from './docs/di/Overview'
import { DIContainer } from './docs/di/Container'
import { DIProviders } from './docs/di/Providers'
import { DIScopes } from './docs/di/Scopes'
import { DIDecorators } from './docs/di/Decorators'
import { DIRequestDAG } from './docs/di/RequestDAG'
import { DIExtractors } from './docs/di/Extractors'
import { DILifecycle } from './docs/di/Lifecycle'
import { DIDiagnostics } from './docs/di/Diagnostics'
import { DIAdvanced } from './docs/di/DIAdvanced'
import { ModelsOverview } from './docs/models/Overview'
import { FieldsOverview } from './docs/models/fields/FieldsOverview'
import { NumericFields } from './docs/models/fields/NumericFields'
import { TextFields } from './docs/models/fields/TextFields'
import { DateTimeFields } from './docs/models/fields/DateTimeFields'
import { StructuredFields } from './docs/models/fields/StructuredFields'
import { ModelsQuerySet } from './docs/models/QuerySet'
import { DefiningRelationships } from './docs/models/relationships/DefiningRelationships'
import { HydrationPrimitives } from './docs/models/relationships/HydrationPrimitives'
import { ManyToManyOperations } from './docs/models/relationships/ManyToManyOperations'
import { AtomicContexts } from './docs/models/transactions/AtomicContexts'
import { Savepoints } from './docs/models/transactions/Savepoints'
import { Hooks } from './docs/models/transactions/Hooks'
import { ModelsSignals } from './docs/models/Signals'
import { ModelsAggregation } from './docs/models/Aggregation'
import { ModelsMigrations } from './docs/models/Migrations'
import { ModelsAdvanced } from './docs/models/Advanced'
import { DatabaseOverview } from './docs/database/Overview'
import { DatabaseEngine } from './docs/database/Engine'
import { DatabaseConfigs } from './docs/database/Configs'
import { SqliteOverview } from './docs/sqlite/Overview'
import { SqliteAPI } from './docs/sqlite/API'
import { SqlitePool } from './docs/sqlite/Pool'
import { SqliteTransactions } from './docs/sqlite/Transactions'
import { SqliteController } from './docs/sqlite/Controller'
import { ContractsOverview } from './docs/contracts/Overview'
import { ContractsFacets } from './docs/contracts/Facets'
import { ContractsProjections } from './docs/contracts/Projections'
import { ContractsLenses } from './docs/contracts/Lenses'
import { ContractsSeals } from './docs/contracts/Seals'
import { ContractsAnnotations } from './docs/contracts/Annotations'
import { ContractsIntegration } from './docs/contracts/Integration'
import { ContractsSchemas } from './docs/contracts/Schemas'
import { ContractsFaults } from './docs/contracts/Faults'
import { AuthOverview } from './docs/auth/Overview'
import { AuthIdentity } from './docs/auth/Identity'
import { AuthCredentials } from './docs/auth/Credentials'
import { AuthManager } from './docs/auth/Manager'
import { AuthOAuth } from './docs/auth/OAuth'
import { AuthMFA } from './docs/auth/MFA'
import { AuthTokens } from './docs/auth/Tokens'
import { AuthStores } from './docs/auth/Stores'
import { AuthFaults } from './docs/auth/Faults'
import { AuthGuards } from './docs/auth/Guards'
import { AuthIntegration } from './docs/auth/Integration'
import { AuthAdvanced } from './docs/auth/Advanced'
import { AuthZOverview } from './docs/authz/Overview'
import { AuthZRBAC } from './docs/authz/RBAC'
import { AuthZABAC } from './docs/authz/ABAC'
import { AuthZPolicies } from './docs/authz/Policies'
import { SessionsOverview } from './docs/sessions/Overview'
import { SessionsIntegration } from './docs/sessions/Integration'
import { SessionsEngine } from './docs/sessions/Engine'
import { SessionsPolicies } from './docs/sessions/Policies'
import { SessionsStores } from './docs/sessions/Stores'
import { SessionsTransport } from './docs/sessions/Transport'
import { SessionsDecorators } from './docs/sessions/Decorators'
import { SessionsState } from './docs/sessions/State'
import { SessionsGuards } from './docs/sessions/Guards'
import { SessionsFaults } from './docs/sessions/Faults'
import { SigningOverview } from './docs/signing/Overview'
import { SigningSigners } from './docs/signing/Signers'
import { SigningSpecialized } from './docs/signing/Specialized'
import { SigningAdvanced } from './docs/signing/Advanced'
import { MiddlewareOverview } from './docs/middleware/Overview'
import { MiddlewareStack } from './docs/middleware/Stack'
import { MiddlewareBuiltIn } from './docs/middleware/BuiltIn'
import { MiddlewareExtended } from './docs/middleware/Extended'
import { MiddlewareCORS } from './docs/middleware/CORS'
import { MiddlewareRateLimit } from './docs/middleware/RateLimit'
import { MiddlewareSecurityHeaders } from './docs/middleware/SecurityHeaders'
import { MiddlewareRequestScope } from './docs/middleware/RequestScope'
import { MiddlewareSession } from './docs/middleware/Session'
import { MiddlewareLogging } from './docs/middleware/Logging'
import { MiddlewareCSP } from './docs/middleware/CSP'
import { MiddlewareCSRF } from './docs/middleware/CSRF'
import { MiddlewareHSTS } from './docs/middleware/HSTS'
import { MiddlewareHTTPSRedirect } from './docs/middleware/HTTPSRedirect'
import { MiddlewareProxyFix } from './docs/middleware/ProxyFix'
import { MiddlewareEffect } from './docs/middleware/EffectMiddleware'
import { HTTPOverview } from './docs/http/Overview'
import { HTTPClient } from './docs/http/Client'
import { HTTPSessions } from './docs/http/Sessions'
import { HTTPTransport } from './docs/http/Transport'
import { HTTPAdvanced } from './docs/http/Advanced'
import { HTTPFaults } from './docs/http/Faults'
import { HTTPIntegration } from './docs/http/Integration'
import { HTTPAPIRequest } from './docs/http/api/Request'
import { HTTPAPIResponse } from './docs/http/api/Response'
import { HTTPAPIAuth } from './docs/http/api/Auth'
import { HTTPAPICookies } from './docs/http/api/Cookies'
import { HTTPAPIMiddleware } from './docs/http/api/Middleware'
import { HTTPAPIMultipart } from './docs/http/api/Multipart'
import { HTTPAPIStreaming } from './docs/http/api/Streaming'
import { WebSocketsOverview } from './docs/websockets/Overview'
import { WebSocketControllers } from './docs/websockets/Controllers'
import { WebSocketRuntime } from './docs/websockets/Runtime'
import { WebSocketAdapters } from './docs/websockets/Adapters'
import { SSEOverview } from './docs/sse/Overview'
import { SSEStandardEvents } from './docs/sse/StandardEvents'
import { SSETextJsonStreams } from './docs/sse/TextJsonStreams'
import { SSEOpenAIStreaming } from './docs/sse/OpenAIStreaming'
import { SSEResourceManagement } from './docs/sse/ResourceManagement'
import { CacheOverview } from './docs/cache/Overview'
import { CacheConfiguration } from './docs/cache/Configuration'
import { CacheCLI } from './docs/cache/CLI'
import { CacheService } from './docs/cache/Service'
import { CacheBackends } from './docs/cache/Backends'
import { CacheDecorators } from './docs/cache/Decorators'
import { CacheAPIReference } from './docs/cache/APIReference'
import { StorageOverview } from './docs/storage/Overview'
import { StorageAPI } from './docs/storage/API'
import { StorageConfiguration } from './docs/storage/Configuration'
import { StorageBackends } from './docs/storage/Backends'
import { StorageController } from './docs/storage/Controller'
import { FilesystemOverview } from './docs/filesystem/Overview'
import { FilesystemAPI } from './docs/filesystem/API'
import { FilesystemOperations } from './docs/filesystem/Operations'
import { FilesystemController } from './docs/filesystem/Controller'
import { I18nOverview } from './docs/i18n/Overview'
import { I18nArchitecture } from './docs/i18n/Architecture'
import { I18nConfiguration } from './docs/i18n/Configuration'
import { I18nIntegration } from './docs/i18n/Integration'
import { I18nAPIReference } from './docs/i18n/APIReference'
import { I18nCLI } from './docs/i18n/CLI'
import { I18nEdgeCases } from './docs/i18n/EdgeCases'
import { I18nTroubleshooting } from './docs/i18n/Troubleshooting'
import { TemplatesOverview } from './docs/templates/Overview'
import { TemplatesEngine } from './docs/templates/Engine'
import { TemplatesLoaders } from './docs/templates/Loaders'
import { TemplatesSecurity } from './docs/templates/Security'
import { MailOverview } from './docs/mail/Overview'
import { MailService } from './docs/mail/Service'
import { MailProviders } from './docs/mail/Providers'
import { MailTemplates } from './docs/mail/Templates'
import { TasksOverview } from './docs/tasks/Overview'
import { TasksAPI } from './docs/tasks/API'
import { TasksConfiguration } from './docs/tasks/Configuration'
import { TasksRetry } from './docs/tasks/Retry'
import { TasksScheduling } from './docs/tasks/Scheduling'
import { TasksController } from './docs/tasks/Controller'
import { CLIOverview } from './docs/cli/Overview'
import { CLICommands } from './docs/cli/Commands'
import { CLIGenerators } from './docs/cli/Generators'
import { CLICoreCommands } from './docs/cli/CoreCommands'
import { CLIDatabaseCommands } from './docs/cli/DatabaseCommands'
import { CLIInspectionCommands } from './docs/cli/InspectionCommands'
import { CLIWebSocketCommands } from './docs/cli/WebSocketCommands'
import { CLIDeployCommands } from './docs/cli/DeployCommands'
import { CLIArtifactCommands } from './docs/cli/ArtifactCommands'
import { CLISubsystemCommands } from './docs/cli/SubsystemCommands'
import { TestingOverview } from './docs/testing/Overview'
import { TestingClient } from './docs/testing/Client'
import { TestingCases } from './docs/testing/Cases'
import { TestingMocks } from './docs/testing/Mocks'
import { TestingRunner } from './docs/testing/Runner'
import { OverviewPage as ProvidersOverview } from './docs/providers/Overview'
import { RenderPage as ProvidersRender } from './docs/providers/Render'
import { SecurityPage as ProvidersSecurity } from './docs/providers/Security'
import { CliPage as ProvidersCli } from './docs/providers/Cli'
import { AquilaryOverview } from './docs/aquilary/Overview'
import { AquilaryManifest } from './docs/aquilary/Manifest'
import { AquilaryRuntime } from './docs/aquilary/Runtime'
import { AquilaryFingerprint } from './docs/aquilary/Fingerprint'
import { EffectsOverview } from './docs/subsystem/Overview'
import { FlowPipelines } from './docs/subsystem/Pipelines'
import { FlowContextNodes } from './docs/subsystem/ContextNodes'
import { FlowLayers } from './docs/subsystem/Layers'
import { EffectsBuiltIn } from './docs/subsystem/BuiltIn'
import { EffectsDBTx } from './docs/subsystem/DBTx'
import { EffectsCacheEffect } from './docs/subsystem/CacheEffect'
import { EffectsQueueEffect } from './docs/subsystem/QueueEffect'
import { EffectsHTTPEffect } from './docs/subsystem/HTTPEffect'
import { EffectsStorageEffect } from './docs/subsystem/StorageEffect'
import { EffectsCustomEffects } from './docs/subsystem/CustomEffects'
import { FaultsOverview } from './docs/faults/Overview'
import { FaultsTaxonomy } from './docs/faults/Taxonomy'
import { FaultsEngine } from './docs/faults/Engine'
import { FaultsHandlers } from './docs/faults/Handlers'
import { FaultsDomains } from './docs/faults/Domains'
import { FaultsAdvanced } from './docs/faults/Advanced'

export function PrintAllDocs() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  useEffect(() => {
    // Delay slightly to allow rendering to complete before triggering print
    const timer = setTimeout(() => {
      window.print()
    }, 2500) // Slightly longer timeout since there are way more pages now

    // Close the print tab after printing/cancelling
    window.onafterprint = () => {
      window.close()
    }

    return () => clearTimeout(timer)
  }, [])

  return (
    <div className={`min-h-screen py-16 px-8 max-w-5xl mx-auto ${isDark ? 'bg-black text-white' : 'bg-white text-gray-900'}`}>
      <style>{`
        @media print {
          body {
            background-color: white !important;
            color: black !important;
          }
          .print-page-break {
            page-break-after: always;
            break-after: page;
          }
          .no-print {
            display: none !important;
          }
        }
      `}</style>
      
      <div className="text-center mb-16 no-print">
        <h1 className="text-3xl font-bold mb-4">Compiling Entire Documentation...</h1>
        <p className="text-gray-400">The print dialog will automatically open. Once complete, this tab will close.</p>
        <p className="text-sm text-yellow-500 mt-2">Note: This compile includes all 130+ sub-sections of documentation. Rendering may take a few seconds.</p>
      </div>

      <div className="space-y-16">
        <div className="print-page-break"><IntroductionPage /></div>
        <div className="print-page-break"><InstallationPage /></div>
        <div className="print-page-break"><QuickStartPage /></div>
        <div className="print-page-break"><DeveloperGuidePage /></div>
        <div className="print-page-break"><ArchitecturePage /></div>
        <div className="print-page-break"><ProjectStructurePage /></div>
        <div className="print-page-break"><AdminSetupPage /></div>
        <div className="print-page-break"><TutorialOverview /></div>
        <div className="print-page-break"><TodoTutorialPage /></div>
        <div className="print-page-break"><AuthTutorialPage /></div>
        <div className="print-page-break"><ServerOverview /></div>
        <div className="print-page-break"><ServerASGI /></div>
        <div className="print-page-break"><ServerLifecycle /></div>
        <div className="print-page-break"><ConfigOverview /></div>
        <div className="print-page-break"><ConfigPyConfig /></div>
        <div className="print-page-break"><ConfigDotEnv /></div>
        <div className="print-page-break"><ConfigWorkspace /></div>
        <div className="print-page-break"><ConfigModule /></div>
        <div className="print-page-break"><ConfigManifest /></div>
        <div className="print-page-break"><ConfigIntegrations /></div>
        <div className="print-page-break"><RequestPage /></div>
        <div className="print-page-break"><ResponsePage /></div>
        <div className="print-page-break"><DataStructuresPage /></div>
        <div className="print-page-break"><UploadsPage /></div>
        <div className="print-page-break"><ControllersOverview /></div>
        <div className="print-page-break"><ControllersRequestCtx /></div>
        <div className="print-page-break"><ControllersFactory /></div>
        <div className="print-page-break"><ControllersEngine /></div>
        <div className="print-page-break"><ControllersCompiler /></div>
        <div className="print-page-break"><ControllersRouter /></div>
        <div className="print-page-break"><ControllersOpenAPI /></div>
        <div className="print-page-break"><ControllersValidation /></div>
        <div className="print-page-break"><ControllersPagination /></div>
        <div className="print-page-break"><ControllersFilters /></div>
        <div className="print-page-break"><ControllersRenderers /></div>
        <div className="print-page-break"><ControllersDecorators /></div>
        <div className="print-page-break"><DecoratorGet /></div>
        <div className="print-page-break"><DecoratorPost /></div>
        <div className="print-page-break"><DecoratorPut /></div>
        <div className="print-page-break"><DecoratorPatch /></div>
        <div className="print-page-break"><DecoratorDelete /></div>
        <div className="print-page-break"><DecoratorHead /></div>
        <div className="print-page-break"><DecoratorOptions /></div>
        <div className="print-page-break"><DecoratorWS /></div>
        <div className="print-page-break"><DecoratorRoute /></div>
        <div className="print-page-break"><RoutingOverview /></div>
        <div className="print-page-break"><RoutingPatterns /></div>
        <div className="print-page-break"><RoutingUrls /></div>
        <div className="print-page-break"><DIOverview /></div>
        <div className="print-page-break"><DIContainer /></div>
        <div className="print-page-break"><DIProviders /></div>
        <div className="print-page-break"><DIScopes /></div>
        <div className="print-page-break"><DIDecorators /></div>
        <div className="print-page-break"><DIRequestDAG /></div>
        <div className="print-page-break"><DIExtractors /></div>
        <div className="print-page-break"><DILifecycle /></div>
        <div className="print-page-break"><DIDiagnostics /></div>
        <div className="print-page-break"><DIAdvanced /></div>
        <div className="print-page-break"><ModelsOverview /></div>
        <div className="print-page-break"><FieldsOverview /></div>
        <div className="print-page-break"><NumericFields /></div>
        <div className="print-page-break"><TextFields /></div>
        <div className="print-page-break"><DateTimeFields /></div>
        <div className="print-page-break"><StructuredFields /></div>
        <div className="print-page-break"><ModelsQuerySet /></div>
        <div className="print-page-break"><DefiningRelationships /></div>
        <div className="print-page-break"><HydrationPrimitives /></div>
        <div className="print-page-break"><ManyToManyOperations /></div>
        <div className="print-page-break"><AtomicContexts /></div>
        <div className="print-page-break"><Savepoints /></div>
        <div className="print-page-break"><Hooks /></div>
        <div className="print-page-break"><ModelsSignals /></div>
        <div className="print-page-break"><ModelsAggregation /></div>
        <div className="print-page-break"><ModelsMigrations /></div>
        <div className="print-page-break"><ModelsAdvanced /></div>
        <div className="print-page-break"><DatabaseOverview /></div>
        <div className="print-page-break"><DatabaseEngine /></div>
        <div className="print-page-break"><DatabaseConfigs /></div>
        <div className="print-page-break"><SqliteOverview /></div>
        <div className="print-page-break"><SqliteAPI /></div>
        <div className="print-page-break"><SqlitePool /></div>
        <div className="print-page-break"><SqliteTransactions /></div>
        <div className="print-page-break"><SqliteController /></div>
        <div className="print-page-break"><ContractsOverview /></div>
        <div className="print-page-break"><ContractsFacets /></div>
        <div className="print-page-break"><ContractsProjections /></div>
        <div className="print-page-break"><ContractsLenses /></div>
        <div className="print-page-break"><ContractsSeals /></div>
        <div className="print-page-break"><ContractsAnnotations /></div>
        <div className="print-page-break"><ContractsIntegration /></div>
        <div className="print-page-break"><ContractsSchemas /></div>
        <div className="print-page-break"><ContractsFaults /></div>
        <div className="print-page-break"><AuthOverview /></div>
        <div className="print-page-break"><AuthIdentity /></div>
        <div className="print-page-break"><AuthCredentials /></div>
        <div className="print-page-break"><AuthManager /></div>
        <div className="print-page-break"><AuthOAuth /></div>
        <div className="print-page-break"><AuthMFA /></div>
        <div className="print-page-break"><AuthTokens /></div>
        <div className="print-page-break"><AuthStores /></div>
        <div className="print-page-break"><AuthFaults /></div>
        <div className="print-page-break"><AuthGuards /></div>
        <div className="print-page-break"><AuthIntegration /></div>
        <div className="print-page-break"><AuthAdvanced /></div>
        <div className="print-page-break"><AuthZOverview /></div>
        <div className="print-page-break"><AuthZRBAC /></div>
        <div className="print-page-break"><AuthZABAC /></div>
        <div className="print-page-break"><AuthZPolicies /></div>
        <div className="print-page-break"><SessionsOverview /></div>
        <div className="print-page-break"><SessionsIntegration /></div>
        <div className="print-page-break"><SessionsEngine /></div>
        <div className="print-page-break"><SessionsPolicies /></div>
        <div className="print-page-break"><SessionsStores /></div>
        <div className="print-page-break"><SessionsTransport /></div>
        <div className="print-page-break"><SessionsDecorators /></div>
        <div className="print-page-break"><SessionsState /></div>
        <div className="print-page-break"><SessionsGuards /></div>
        <div className="print-page-break"><SessionsFaults /></div>
        <div className="print-page-break"><SigningOverview /></div>
        <div className="print-page-break"><SigningSigners /></div>
        <div className="print-page-break"><SigningSpecialized /></div>
        <div className="print-page-break"><SigningAdvanced /></div>
        <div className="print-page-break"><MiddlewareOverview /></div>
        <div className="print-page-break"><MiddlewareStack /></div>
        <div className="print-page-break"><MiddlewareBuiltIn /></div>
        <div className="print-page-break"><MiddlewareExtended /></div>
        <div className="print-page-break"><MiddlewareCORS /></div>
        <div className="print-page-break"><MiddlewareRateLimit /></div>
        <div className="print-page-break"><MiddlewareSecurityHeaders /></div>
        <div className="print-page-break"><MiddlewareRequestScope /></div>
        <div className="print-page-break"><MiddlewareSession /></div>
        <div className="print-page-break"><MiddlewareLogging /></div>
        <div className="print-page-break"><MiddlewareCSP /></div>
        <div className="print-page-break"><MiddlewareCSRF /></div>
        <div className="print-page-break"><MiddlewareHSTS /></div>
        <div className="print-page-break"><MiddlewareHTTPSRedirect /></div>
        <div className="print-page-break"><MiddlewareProxyFix /></div>
        <div className="print-page-break"><MiddlewareEffect /></div>
        <div className="print-page-break"><HTTPOverview /></div>
        <div className="print-page-break"><HTTPClient /></div>
        <div className="print-page-break"><HTTPSessions /></div>
        <div className="print-page-break"><HTTPTransport /></div>
        <div className="print-page-break"><HTTPAdvanced /></div>
        <div className="print-page-break"><HTTPFaults /></div>
        <div className="print-page-break"><HTTPIntegration /></div>
        <div className="print-page-break"><HTTPAPIRequest /></div>
        <div className="print-page-break"><HTTPAPIResponse /></div>
        <div className="print-page-break"><HTTPAPIAuth /></div>
        <div className="print-page-break"><HTTPAPICookies /></div>
        <div className="print-page-break"><HTTPAPIMiddleware /></div>
        <div className="print-page-break"><HTTPAPIMultipart /></div>
        <div className="print-page-break"><HTTPAPIStreaming /></div>
        <div className="print-page-break"><WebSocketsOverview /></div>
        <div className="print-page-break"><WebSocketControllers /></div>
        <div className="print-page-break"><WebSocketRuntime /></div>
        <div className="print-page-break"><WebSocketAdapters /></div>
        <div className="print-page-break"><SSEOverview /></div>
        <div className="print-page-break"><SSEStandardEvents /></div>
        <div className="print-page-break"><SSETextJsonStreams /></div>
        <div className="print-page-break"><SSEOpenAIStreaming /></div>
        <div className="print-page-break"><SSEResourceManagement /></div>
        <div className="print-page-break"><CacheOverview /></div>
        <div className="print-page-break"><CacheConfiguration /></div>
        <div className="print-page-break"><CacheCLI /></div>
        <div className="print-page-break"><CacheService /></div>
        <div className="print-page-break"><CacheBackends /></div>
        <div className="print-page-break"><CacheDecorators /></div>
        <div className="print-page-break"><CacheAPIReference /></div>
        <div className="print-page-break"><StorageOverview /></div>
        <div className="print-page-break"><StorageAPI /></div>
        <div className="print-page-break"><StorageConfiguration /></div>
        <div className="print-page-break"><StorageBackends /></div>
        <div className="print-page-break"><StorageController /></div>
        <div className="print-page-break"><FilesystemOverview /></div>
        <div className="print-page-break"><FilesystemAPI /></div>
        <div className="print-page-break"><FilesystemOperations /></div>
        <div className="print-page-break"><FilesystemController /></div>
        <div className="print-page-break"><I18nOverview /></div>
        <div className="print-page-break"><I18nArchitecture /></div>
        <div className="print-page-break"><I18nConfiguration /></div>
        <div className="print-page-break"><I18nIntegration /></div>
        <div className="print-page-break"><I18nAPIReference /></div>
        <div className="print-page-break"><I18nCLI /></div>
        <div className="print-page-break"><I18nEdgeCases /></div>
        <div className="print-page-break"><I18nTroubleshooting /></div>
        <div className="print-page-break"><TemplatesOverview /></div>
        <div className="print-page-break"><TemplatesEngine /></div>
        <div className="print-page-break"><TemplatesLoaders /></div>
        <div className="print-page-break"><TemplatesSecurity /></div>
        <div className="print-page-break"><MailOverview /></div>
        <div className="print-page-break"><MailService /></div>
        <div className="print-page-break"><MailProviders /></div>
        <div className="print-page-break"><MailTemplates /></div>
        <div className="print-page-break"><TasksOverview /></div>
        <div className="print-page-break"><TasksAPI /></div>
        <div className="print-page-break"><TasksConfiguration /></div>
        <div className="print-page-break"><TasksRetry /></div>
        <div className="print-page-break"><TasksScheduling /></div>
        <div className="print-page-break"><TasksController /></div>
        <div className="print-page-break"><CLIOverview /></div>
        <div className="print-page-break"><CLICommands /></div>
        <div className="print-page-break"><CLIGenerators /></div>
        <div className="print-page-break"><CLICoreCommands /></div>
        <div className="print-page-break"><CLIDatabaseCommands /></div>
        <div className="print-page-break"><CLIInspectionCommands /></div>
        <div className="print-page-break"><CLIWebSocketCommands /></div>
        <div className="print-page-break"><CLIDeployCommands /></div>
        <div className="print-page-break"><CLIArtifactCommands /></div>
        <div className="print-page-break"><CLISubsystemCommands /></div>
        <div className="print-page-break"><TestingOverview /></div>
        <div className="print-page-break"><TestingClient /></div>
        <div className="print-page-break"><TestingCases /></div>
        <div className="print-page-break"><TestingMocks /></div>
        <div className="print-page-break"><TestingRunner /></div>
        <div className="print-page-break"><ProvidersOverview /></div>
        <div className="print-page-break"><ProvidersRender /></div>
        <div className="print-page-break"><ProvidersSecurity /></div>
        <div className="print-page-break"><ProvidersCli /></div>
        <div className="print-page-break"><AquilaryOverview /></div>
        <div className="print-page-break"><AquilaryManifest /></div>
        <div className="print-page-break"><AquilaryRuntime /></div>
        <div className="print-page-break"><AquilaryFingerprint /></div>
        <div className="print-page-break"><EffectsOverview /></div>
        <div className="print-page-break"><FlowPipelines /></div>
        <div className="print-page-break"><FlowContextNodes /></div>
        <div className="print-page-break"><FlowLayers /></div>
        <div className="print-page-break"><EffectsBuiltIn /></div>
        <div className="print-page-break"><EffectsDBTx /></div>
        <div className="print-page-break"><EffectsCacheEffect /></div>
        <div className="print-page-break"><EffectsQueueEffect /></div>
        <div className="print-page-break"><EffectsHTTPEffect /></div>
        <div className="print-page-break"><EffectsStorageEffect /></div>
        <div className="print-page-break"><EffectsCustomEffects /></div>
        <div className="print-page-break"><FaultsOverview /></div>
        <div className="print-page-break"><FaultsTaxonomy /></div>
        <div className="print-page-break"><FaultsEngine /></div>
        <div className="print-page-break"><FaultsHandlers /></div>
        <div className="print-page-break"><FaultsDomains /></div>
        <div className="print-page-break"><FaultsAdvanced /></div>
        <div className="print-page-break">
          <h1 className="text-4xl font-bold mb-8">Releases</h1>
          <Releases printMode={true} />
        </div>
        <div>
          <h1 className="text-4xl font-bold mb-8">Changelogs</h1>
          <Changelogs printMode={true} />
        </div>
      </div>
    </div>
  )
}
